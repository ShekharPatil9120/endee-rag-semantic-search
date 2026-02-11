import os
import sys
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_dashboard.settings')
import django
django.setup()

from detection.views import run_prediction
from utils.email_utils import send_action_notification
from django.contrib.auth.models import User


def main():
    remote_base = "https://shekharpatil2004.pythonanywhere.com/photos/"
    try:
        r = requests.get(remote_base, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print('Error fetching remote page:', e)
        sys.exit(1)

    soup = BeautifulSoup(r.text, 'html.parser')
    imgs = soup.find_all('img')
    if not imgs:
        print('No images found on remote page')
        sys.exit(1)

    img_tag = imgs[0]
    src = img_tag.get('src')
    if not src:
        print('Image tag missing src')
        sys.exit(1)

    image_url = urljoin(remote_base, src)

    try:
        resp = requests.get(image_url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print('Error downloading image:', e)
        sys.exit(1)

    try:
        pil_img = Image.open(BytesIO(resp.content)).convert('RGB')
    except Exception as e:
        print('Error opening image:', e)
        sys.exit(1)

    result = run_prediction(pil_img)
    label = result.get('label') if isinstance(result, dict) else str(result)
    confidence = result.get('confidence') if isinstance(result, dict) else None

    email_sent = False
    try:
        if label and label.lower() != 'healthy':
            user = User.objects.filter(is_active=True).first()
            if user:
                email_sent = bool(send_action_notification(user, 'Disease Detected', f'Disease: {label}'))
    except Exception:
        email_sent = False

    print('Image URL:', image_url)
    if confidence is not None:
        print('Prediction:', f"{label} ({confidence}%)")
    else:
        print('Prediction:', label)
    print('Email Sent:', email_sent)


if __name__ == '__main__':
    main()
