import os
import tempfile
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from django.core.cache import cache

from utils.email_utils import send_action_notification


def run_model(image_path):
    return "Blight"


def process_latest_remote_image():
    try:
        remote_base = "https://shekharpatil2004.pythonanywhere.com/photos/"
        resp = requests.get(remote_base, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        imgs = soup.find_all("img")
        if not imgs:
            return "no_new_image"
        img_tag = imgs[0]
        src = img_tag.get("src")
        if not src:
            return "no_new_image"
        image_url = urljoin(remote_base, src)
        parsed = urlparse(image_url)
        image_name = os.path.basename(parsed.path)

        last_name = cache.get("last_image_name")
        if last_name == image_name:
            return "no_new_image"

        r = requests.get(image_url, timeout=15)
        r.raise_for_status()

        suffix = os.path.splitext(image_name)[1] or ".jpg"
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        try:
            tf.write(r.content)
            tf.flush()
            tf_path = tf.name
        finally:
            tf.close()

        label = run_model(tf_path)

        try:
            from django.contrib.auth.models import User
            user = User.objects.filter(is_active=True).first()
        except Exception:
            user = None

        try:
            from .models import DetectionRecord
            dr_model = DetectionRecord
        except Exception:
            dr_model = None

        if dr_model is not None:
            try:
                field_names = [f.name for f in dr_model._meta.fields]
                kwargs = {}
                if "predicted_disease" in field_names:
                    kwargs["predicted_disease"] = label
                if "label" in field_names and "predicted_disease" not in field_names:
                    kwargs["label"] = label
                if "image_url" in field_names:
                    kwargs["image_url"] = image_url
                try:
                    dr_model.objects.create(**kwargs)
                except Exception:
                    pass
            except Exception:
                pass

        cache.set("latest_detection", {"label": label, "image_url": image_url}, None)
        cache.set("last_image_name", image_name, None)

        if user is not None:
            try:
                send_action_notification(user, "Disease Detected", f"Disease: {label}")
            except Exception:
                pass

        try:
            os.unlink(tf_path)
        except Exception:
            pass

        return "detected"
    except Exception:
        return "error"
