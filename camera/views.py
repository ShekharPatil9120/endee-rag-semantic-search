import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CameraIP

# Optional local media dir (kept for compatibility)
MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"


# --- Show Photos Page (reads live images from hosted PythonAnywhere site) ---
def show_photos(request):
    """
    Fetches live images from the hosted PythonAnywhere web
    and displays them using the camera app's internal template.
    """
    remote_base_url = "https://shekharpatil2004.pythonanywhere.com/photos/"

    try:
        response = requests.get(remote_base_url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        img_tags = soup.find_all("img")
        photos = []

        for img in img_tags[:6]:  # only latest 6 photos
            img_url = urljoin(remote_base_url, img.get("src"))
            photos.append({
                "image_url": img_url,
                "uploaded_at": "Live"  # placeholder
            })
    except Exception as e:
        photos = []
        print("⚠️ Error fetching remote images:", e)

    # Fetch saved camera IP or fallback default
    ip_obj = CameraIP.objects.first()
    camera_ip = ip_obj.ip_address if ip_obj else "http://10.249.11.206:8080"

    # ✅ Updated template path (now inside app)
    return render(request, "camera/photos.html", {
        "photos": photos,
        "camera_ip": camera_ip
    })


# --- Edit Camera IP ---
@csrf_exempt
def edit_ip(request):
    """
    Handles getting or updating the saved camera IP address.
    """
    if request.method == "POST":
        data = json.loads(request.body)
        new_ip = data.get("ip_address", "").strip()
        ip_obj, created = CameraIP.objects.get_or_create(id=1)
        ip_obj.ip_address = new_ip
        ip_obj.save()
        return JsonResponse({"status": "success", "ip": new_ip})

    # For GET requests, return current IP
    ip_obj = CameraIP.objects.first()
    current_ip = ip_obj.ip_address if ip_obj else "http://10.249.11.206:8080"
    return JsonResponse({"status": "success", "ip": current_ip})
