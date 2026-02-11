from django.core.cache import cache
import time


def should_send_sensor_email(user, new_data, cooldown_seconds=300):
	if not hasattr(user, 'id'):
		return False
	uid = getattr(user, 'id')
	data_key = f"last_sensor_data_{uid}"
	time_key = f"last_sensor_email_ts_{uid}"

	last_data = cache.get(data_key)
	last_ts = cache.get(time_key) or 0
	now = time.time()

	if last_data == new_data:
		return False

	if now - last_ts < cooldown_seconds:
		return False

	cache.set(data_key, new_data, None)
	cache.set(time_key, now, cooldown_seconds)
	return True
