# debug_aws.py
import os
import django
from django.conf import settings

print("=== 1. TESTING DECOUPLE ===")
try:
    from decouple import config
    print("✅ decouple imported successfully")
    print("AWS_ACCESS_KEY_ID:", config('AWS_ACCESS_KEY_ID', default='NOT_FOUND'))
    print("AWS_SECRET (first 10):", config('AWS_SECRET_ACCESS_KEY', default='NOT_FOUND')[:10])
    print("AWS_SES_REGION:", config('AWS_SES_REGION', default='NOT_FOUND'))
except Exception as e:
    print("❌ decouple error:", e)

print("\n=== 2. TESTING DJANGO SETTINGS ===")
print("Django AWS_ACCESS_KEY_ID:", getattr(settings, 'AWS_ACCESS_KEY_ID', 'NOT_SET'))
print("Django AWS_SECRET (first 10):", str(getattr(settings, 'AWS_SECRET_ACCESS_KEY', 'NOT_SET'))[:10])
print("Django AWS_SES_REGION_NAME:", getattr(settings, 'AWS_SES_REGION_NAME', 'NOT_SET'))

print("\n=== 3. TESTING OS ENVIRONMENT ===")
print("OS AWS_ACCESS_KEY_ID:", os.environ.get('AWS_ACCESS_KEY_ID', 'NOT_IN_ENV'))
print("OS AWS_SECRET (first 10):", os.environ.get('AWS_SECRET_ACCESS_KEY', 'NOT_IN_ENV')[:10])

print("\n=== 4. MANUAL CREDENTIAL TEST ===")
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAXL2RUO72KOXKMTFW'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'BC3qMPF7RFCKYozf2tbsSddTZ284sr26LNbcJr0Dbut3'
os.environ['AWS_SES_REGION_NAME'] = 'eu-north-1'
print("✅ Manual credentials set")

print("\n=== 5. TEST BOTO3 CONNECTION ===")
try:
    import boto3
    client = boto3.client('ses', region_name='eu-north-1')
    quota = client.get_send_quota()
    print("✅ boto3 connection successful:", quota)
except Exception as e:
    print("❌ boto3 error:", e)