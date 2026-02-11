from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_GET
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import feedparser
import requests
import json

from .forms import RegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile, CommunityPost, Comment
from utils.email_utils import send_action_notification
from utils.sensor_utils import should_send_sensor_email
from crop_api.models import Recommendation


# --------------------------
# Register View
# --------------------------
@never_cache
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


# --------------------------
# Login View
# --------------------------
@never_cache
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'accounts/login.html')


# --------------------------
# Logout View
# --------------------------
@never_cache
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


# --------------------------
# Sensor Data API Endpoint (for external IoT devices to POST sensor readings)
# -----------------------
@csrf_exempt
@require_http_methods(["POST"])
def sensor_data_endpoint(request):
    """
    Accept sensor data from IoT devices.
    Expected JSON: {"temperature": X, "humidity": Y, "moisture": Z, "air_quality": W}
    Returns: {"status": "success"} or {"status": "error", "message": "..."}
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    
    # Optional: Store sensor data in cache or DB for later retrieval
    cache.set("latest_sensor_data", data, timeout=3600)  # Store for 1 hour
    
    return JsonResponse({"status": "success", "message": "Sensor data received"})


# Home View (Live Sensor Data)
# --------------------------
# --------------------------
# Home View (Live Sensor Data)
# --------------------------
@login_required
@never_cache
def home_view(request):
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    from django.core.cache import cache
    from django.urls import reverse

    # ---------------- SENSOR DATA ----------------
    api_url = "https://shekharpatil202.pythonanywhere.com/get-latest/"
    try:
        response = requests.get(api_url, timeout=5)
        data = response.json() if response.status_code == 200 else {}
    except Exception:
        data = {}

    sensor_data = {
        "temperature": data.get("temperature", 0),
        "humidity": data.get("humidity", 0),
        "moisture": data.get("moisture", 0),
        "air_quality": data.get("air_quality", 0),
    }

    # AJAX request → return JSON only
    if request.GET.get("ajax") == "1":

        # ---------------- EMAIL ON SENSOR CHANGE ----------------
        try:
            if request.user.is_authenticated and should_send_sensor_email(request.user, sensor_data):
                send_action_notification(
                    request.user,
                    "Sensor Data Updated",
                    f"New sensor readings: {sensor_data}"
                )
        except:
            pass

        extra = {
            "recommended_crop": None,
            "detected_disease": None,
            "camera_image_url": None,
            "motor_state": None,
        }

        # ---------------- RECOMMENDED CROP ----------------
        try:
            latest_reco = Recommendation.objects.order_by("-created_at").first()
            extra["recommended_crop"] = latest_reco.recommended_crop if latest_reco else None
        except:
            extra["recommended_crop"] = None

        # ---------------- DISEASE DETECTION (CACHE) ----------------
        det = cache.get("latest_detection")
        if det and isinstance(det, dict):
            extra["detected_disease"] = det.get("label")
        else:
            extra["detected_disease"] = None

        # ---------------- REMOTE ESP32-CAM IMAGE ----------------
        try:
            remote_url = "https://shekharpatil2004.pythonanywhere.com/photos/"
            resp = requests.get(remote_url, timeout=5)
            soup = BeautifulSoup(resp.text, "html.parser")
            imgs = soup.find_all("img")
            extra["camera_image_url"] = urljoin(remote_url, imgs[0].get("src")) if imgs else None
        except:
            extra["camera_image_url"] = None

        # ---------------- MOTOR STATE (READ FROM SAME PROXY USED IN motor.html) ----------------


        # ---------------- FINAL JSON RESPONSE ----------------
        return JsonResponse({**sensor_data, **extra})

    # Render full page
    return render(request, "accounts/home.html", {"sensor_data": sensor_data})



# --------------------------
# Dashboard View
# --------------------------
@login_required
@never_cache
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')


@login_required
def motor_view(request):
    return render(request, 'accounts/motor.html')


@login_required
@require_GET
def motor_set_proxy(request):
    """Proxy endpoint: forwards motor set requests to the external API,
    then sends a notification email to the authenticated user.
    """
    state = request.GET.get('set')
    if state is None:
        return JsonResponse({'error': 'missing "set" parameter'}, status=400)

    external = 'https://shekharpatil.pythonanywhere.com/api/update-set/'
    try:
        resp = requests.get(external, params={'set': state}, timeout=10)
        # prefer JSON when available
        try:
            payload = resp.json()
        except Exception:
            payload = resp.text
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=502)

    # send notification email (non-blocking)
    try:
        if hasattr(request, 'user') and request.user.is_authenticated:
            readable = 'ON' if str(state) == '1' else 'OFF'
            send_action_notification(request.user, 'Motor State Changed', f'Irrigation motor set to {readable}.')
    except Exception:
        pass

    return JsonResponse({'status': resp.status_code, 'response': payload}, status=200)


@login_required
@require_GET
def motor_read_proxy(request):
    """Proxy endpoint: fetches motor state from external API and returns it."""
    external = 'https://shekharpatil.pythonanywhere.com/api/read/'
    try:
        resp = requests.get(external, timeout=10)
        try:
            payload = resp.json()
        except Exception:
            payload = resp.text
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=502)

    # If payload is already a dict/list, return as JSON; otherwise wrap it.
    try:
        return JsonResponse(payload, safe=False, status=resp.status_code)
    except TypeError:
        return JsonResponse({'response': payload}, status=resp.status_code)


# --------------------------
# Profile View
# --------------------------
@login_required
@never_cache
def profile_view(request):
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


# --------------------------
# Contact Admin View
# --------------------------
@login_required
def contact_admin_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        subject = f"📩 Message from {name} ({email})"
        full_message = f"Sender Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

        try:
            send_mail(
                subject,
                full_message,
                settings.EMAIL_HOST_USER,     # from email
                ["shekharpatil9120@gmail.com"],  # to email
                fail_silently=False,
            )
            messages.success(request, "✅ Your message has been sent successfully!")
        except Exception as e:
            messages.error(request, f"❌ Failed to send message: {e}")

        return redirect("contact_admin")

    return render(request, "accounts/contact_admin.html")



# --------------------------
# Contact Specialist View
# --------------------------
@login_required
def contact_specialist_view(request):
    return render(request, 'accounts/contact_specialist.html')


# --------------------------
# Community Views
# --------------------------
@login_required
def community_view(request):
    posts = CommunityPost.objects.all().order_by('-created_at')
    return render(request, 'accounts/community.html', {'posts': posts})


@login_required
def add_post_view(request):
    if request.method == 'POST':
        title = request.POST['title']
        content = request.POST['content']
        CommunityPost.objects.create(author=request.user, title=title, content=content)
        return redirect('community')
    return render(request, 'accounts/add_post.html')


@login_required
def delete_post_view(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    if post.can_delete(request.user):
        post.delete()
    return redirect('community')


@login_required
def add_comment_view(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            Comment.objects.create(post=post, author=request.user, text=text)
    return redirect('community')


@login_required
def delete_comment_view(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.can_delete(request.user):
        comment.delete()
    return redirect('community')


# --------------------------
# 📰 Agricultural News View
# --------------------------
@login_required
def agri_news(request):
    api_key = "dcb2ad47b9bd422786640e9d3bc3faf4"
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q=agriculture+india&language=en&sortBy=publishedAt&apiKey={api_key}"
    )

    news_items = []
    try:
        response = requests.get(url, timeout=10)
        print("API STATUS:", response.status_code)

        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])[:20]  # ✅ only top 20
            print("TOTAL ARTICLES:", len(articles))

            for article in articles:
                news_items.append({
                    "title": article.get("title"),
                    "summary": article.get("description") or "No summary available.",
                    "link": article.get("url"),
                    "published": (
                        article.get("publishedAt")[:10]
                        if article.get("publishedAt") else "Unknown date"
                    ),
                })
        else:
            print("⚠️ API returned error:", response.text)
    except Exception as e:
        print("❌ ERROR fetching news:", e)

    return render(request, "accounts/news.html", {"news_items": news_items})

def motor_control(request):
    # Get district (location) from URL or form — default is Belagavi
    location = request.GET.get("location", "Belagavi")

    api_key = "bfc9cd3b74614beeb59172239250411"
    url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=1&aqi=no&alerts=no"

    response = requests.get(url)
    data = response.json()

    if "error" in data:
        weather = {"error": data["error"]["message"]}
    else:
        weather = {
            "location": data["location"]["name"],
            "region": data["location"]["region"],
            "temp_c": data["current"]["temp_c"],
            "condition": data["current"]["condition"]["text"],
            "icon": data["current"]["condition"]["icon"],
            "humidity": data["current"]["humidity"],
            "chance_of_rain": data["forecast"]["forecastday"][0]["day"]["daily_chance_of_rain"],
        }

    # send notification email to authenticated user (non-blocking)
    try:
        if hasattr(request, 'user') and request.user.is_authenticated:
            msg = (
                f"Location: {weather.get('location')} ({weather.get('region')})\n"
                f"Temperature (C): {weather.get('temp_c')}\n"
                f"Condition: {weather.get('condition')}\n"
                f"Humidity: {weather.get('humidity')}\n"
                f"Chance of rain: {weather.get('chance_of_rain')}%"
            )
            send_action_notification(request.user, 'Weather Prediction', msg)
    except Exception:
        pass

    return render(request, "motor_control.html", {"weather": weather})
