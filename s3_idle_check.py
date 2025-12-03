# s3_idle_check.py
import boto3
from datetime import datetime, timedelta, timezone

BUCKET_NAME = "your-bucket-name"
REGION = "ap-south-1"

cloudwatch = boto3.client("cloudwatch", region_name=REGION)

def get_storage_metrics(bucket):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=2)
    queries = [
        {
            "Id": "size",
            "MetricStat": {
                "Metric": {"Namespace": "AWS/S3","MetricName": "BucketSizeBytes",
                    "Dimensions":[{"Name": "BucketName","Value": bucket},{"Name": "StorageType","Value": "StandardStorage"}]},
                "Period": 86400,"Stat": "Average"
            },
            "ReturnData": True
        },
        {
            "Id": "objects",
            "MetricStat": {
                "Metric": {"Namespace": "AWS/S3","MetricName": "NumberOfObjects",
                    "Dimensions":[{"Name": "BucketName","Value": bucket},{"Name": "StorageType","Value": "AllStorageTypes"}]},
                "Period": 86400,"Stat": "Average"
            },
            "ReturnData": True
        }
    ]
    resp = cloudwatch.get_metric_data(MetricDataQueries=queries, StartTime=start, EndTime=now)
    size_gb = 0; obj_count = 0
    for r in resp["MetricDataResults"]:
        if r["Id"] == "size" and r.get("Values"): size_gb = r["Values"][0]/(1024**3)
        if r["Id"] == "objects" and r.get("Values"): obj_count = int(r["Values"][0])
    return round(size_gb,3), obj_count

def get_request_activity(bucket):
    now = datetime.now(timezone.utc); start = now - timedelta(hours=1)
    resp = cloudwatch.get_metric_data(
        MetricDataQueries=[{
            "Id":"requests",
            "MetricStat":{
                "Metric":{"Namespace":"AWS/S3","MetricName":"AllRequests",
                    "Dimensions":[{"Name":"BucketName","Value":bucket},{"Name":"FilterId","Value":"EntireBucket"}]},
                "Period":300,"Stat":"Sum"},
            "ReturnData":True}],
        StartTime=start,EndTime=now)
    vals=resp["MetricDataResults"][0].get("Values",[])
    return int(vals[0]) if vals else 0

if __name__=="__main__":
    print("\n--- S3 Idle Check Report ---")
    size,obj=get_storage_metrics(BUCKET_NAME)
    req=get_request_activity(BUCKET_NAME)
    print(f"Bucket: {BUCKET_NAME}\nBucket Size (GB): {size}\nObject Count: {obj}\nRequests (last 1 hr): {req}")
    if size<1 and obj<50 and req<20: print("\nSTATUS: Bucket appears idle / underutilized.")
    else: print("\nSTATUS: Bucket is actively used.")
