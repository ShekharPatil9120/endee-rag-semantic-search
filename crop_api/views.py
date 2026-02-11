from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
import pandas as pd
import requests
from utils.email_utils import send_action_notification

# ✅ Load CSV once
df = pd.read_csv('crop_api/crop_data.csv')

# ✅ PROXY ENDPOINT - Fetch sensor data from external API (bypasses CORS)
def get_live_sensor_data(request):
    """
    Proxy endpoint to fetch live sensor data from external API.
    Frontend calls http://localhost:8000/get-live-sensors/ instead of
    https://shekharpatil202.pythonanywhere.com/get-latest/
    This avoids CORS errors because request is server-to-server, not browser-to-external.
    """
    try:
        external_url = "https://shekharpatil202.pythonanywhere.com/get-latest/"
        response = requests.get(external_url, timeout=5)
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({"error": "External API error", "status": response.status_code}, status=500)
    except requests.exceptions.Timeout:
        return JsonResponse({"error": "Request timeout"}, status=504)
    except requests.exceptions.ConnectionError:
        return JsonResponse({"error": "Connection error"}, status=503)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def find_best_match(temp, hum, N, P, K, air_quality, month_start, month_end):
    df['score'] = (
        (df['Temperature'] - temp)**2 +
        (df['Humidity'] - hum)**2 +
        (df['Nitrogen'] - N)**2 +
        (df['Phosphorus'] - P)**2 +
        (df['Potassium'] - K)**2 +
        (df['Air_Quality'] - air_quality)**2 +
        ((df['Month_Start'] - month_start)**2 + (df['Month_End'] - month_end)**2)*0.5
    )
    best_match = df.loc[df['score'].idxmin()]
    return {
        "most_recommended": best_match['Most_Recommended'],
        "possible_cultivation": best_match['Possible_Cultivation'],
        "suggestions": best_match['Suggestions']
    }

# ✅ Front page view (renders HTML)
def index(request):
    if request.method == 'POST':
        temp = float(request.POST.get('temperature', 0))
        hum = float(request.POST.get('humidity', 0))
        # Default NPK values since no NPK sensors are available
        N = 90.0
        P = 42.0
        K = 43.0
        air_quality = float(request.POST.get('air_quality', 0))
        month_start = int(request.POST.get('month_start', 1))
        month_end = int(request.POST.get('month_end', 12))

        result = find_best_match(temp, hum, N, P, K, air_quality, month_start, month_end)

        # send notification to authenticated user (minimal, non-intrusive)
        try:
            if request.user.is_authenticated:
                msg = (
                    f"Most recommended: {result.get('most_recommended')}\n"
                    f"Possible cultivation: {result.get('possible_cultivation')}\n\n"
                    f"Suggestions:\n{result.get('suggestions')}"
                )
                send_action_notification(request.user, 'Crop Recommendation', msg)
        except Exception:
            pass

        # SAVE recommendation into DB (the missing part)
        if request.user.is_authenticated:
            from crop_api.models import Recommendation
            Recommendation.objects.create(
                user=request.user,
                recommended_crop=result.get('most_recommended'),
                possible_cultivation=result.get('possible_cultivation'),
                suggestions=result.get('suggestions')
            )

        return render(request, 'crop_api/index.html', {'result': result})

    return render(request, 'crop_api/index.html')

# ✅ API view (for POST requests)
class CropRecommendationAPI(APIView):
    def post(self, request):
        data = request.data
        temp = float(data.get('temperature', 0))
        hum = float(data.get('humidity', 0))
        # Use default NPK values (no NPK sensors)
        N = float(data.get('nitrogen', 90))
        P = float(data.get('phosphorus', 42))
        K = float(data.get('potassium', 43))
        air_quality = float(data.get('air_quality', 0))
        month_start = int(data.get('month_start', 1))
        month_end = int(data.get('month_end', 12))

        result = find_best_match(temp, hum, N, P, K, air_quality, month_start, month_end)
        # send notification when user is authenticated
        try:
            if hasattr(request, 'user') and request.user.is_authenticated:
                msg = (
                    f"Most recommended: {result.get('most_recommended')}\n"
                    f"Possible cultivation: {result.get('possible_cultivation')}\n\n"
                    f"Suggestions:\n{result.get('suggestions')}"
                )
                send_action_notification(request.user, 'Crop Recommendation', msg)
        except Exception:
            pass
        # Save recommendation
        if request.user.is_authenticated:
            try:
                from crop_api.models import Recommendation
                Recommendation.objects.create(
                    user=request.user,
                    recommended_crop=result.get('most_recommended'),
                    possible_cultivation=result.get('possible_cultivation'),
                    suggestions=result.get('suggestions')
                )
            except Exception:
                pass
        return Response(result)
