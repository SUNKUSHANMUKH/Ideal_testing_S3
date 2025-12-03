# s3_usage_monitor.py
import boto3
from datetime import datetime, timedelta, timezone

BUCKET_NAME = "your-bucket-name"
REGION = "ap-south-1"

cloudwatch = boto3.client("cloudwatch", region_name=REGION)

def fetch_metric(namespace, metric, dims, period, stat, start, end):
    resp = cloudwatch.get_metric_data(
        MetricDataQueries=[{
            "Id":"m",
            "MetricStat":{"Metric":{"Namespace":namespace,"MetricName":metric,"Dimensions":dims},
                          "Period":period,"Stat":stat},
            "ReturnData":True}],
        StartTime=start,EndTime=end)
    vals = resp["MetricDataResults"][0].get("Values",[])
    return vals[0] if vals else 0

def get_bucket_usage(bucket):
    now = datetime.now(timezone.utc)
    sd = now - timedelta(days=2)
    sh = now - timedelta(hours=1)

    size_bytes = fetch_metric("AWS/S3","BucketSizeBytes",
        [{"Name":"BucketName","Value":bucket},{"Name":"StorageType","Value":"StandardStorage"}],
        86400,"Average",sd,now)

    obj_count = fetch_metric("AWS/S3","NumberOfObjects",
        [{"Name":"BucketName","Value":bucket},{"Name":"StorageType","Value":"AllStorageTypes"}],
        86400,"Average",sd,now)

    f=[{"Name":"BucketName","Value":bucket},{"Name":"FilterId","Value":"EntireBucket"}]

    allreq = fetch_metric("AWS/S3","AllRequests",f,300,"Sum",sh,now)
    getreq = fetch_metric("AWS/S3","GetRequests",f,300,"Sum",sh,now)
    putreq = fetch_metric("AWS/S3","PutRequests",f,300,"Sum",sh,now)
    down = fetch_metric("AWS/S3","BytesDownloaded",f,300,"Sum",sh,now)
    up = fetch_metric("AWS/S3","BytesUploaded",f,300,"Sum",sh,now)
    e4 = fetch_metric("AWS/S3","4xxErrors",f,300,"Sum",sh,now)
    e5 = fetch_metric("AWS/S3","5xxErrors",f,300,"Sum",sh,now)

    return {
        "BucketSizeGB": round(size_bytes/(1024**3),3),
        "ObjectCount": int(obj_count),
        "AllRequests": int(allreq),
        "GetRequests": int(getreq),
        "PutRequests": int(putreq),
        "BytesDownloadedMB": round(down/(1024**2),2),
        "BytesUploadedMB": round(up/(1024**2),2),
        "4xxErrors": int(e4),
        "5xxErrors": int(e5)
    }

if __name__=="__main__":
    print("\n--- S3 Usage Monitoring Report ---")
    d=get_bucket_usage(BUCKET_NAME)
    for k,v in d.items(): print(f"{k}: {v}")
