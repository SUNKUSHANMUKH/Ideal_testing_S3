---

Prerequisites & safety notes (read this first)

1. **Do NOT** put long-lived access keys into source code or commit them. Use an **EC2 instance role** (Instance Profile) or `aws configure` on a secure machine. If you included keys earlier, rotate/delete them immediately in IAM.
2. You need an account with permissions to create/attach IAM roles, enable Cost Explorer, and view CloudWatch and S3.
3. I used `GetMetricData` (recommended for multi-metric queries and larger ranges) — it supports more metrics per call and metric math. ([AWS Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_GetMetricData.html?utm_source=chatgpt.com))

---

# 📂 Procedure:

## **1. Enable Cost Explorer in Billing console (first!)**

- Go to AWS Console → Billing → Cost Explorer → Enable Cost Explorer. API requests to Cost Explorer will fail until this is enabled. (Do this before running CE API calls). ([AWS Documentation](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostAndUsage.html?utm_source=chatgpt.com))

## **2. Create IAM role for monitoring and attach to the EC2 instance (recommended)**

- Create role: Service → EC2 → Next: permissions.
- Policy (minimal, follow least privilege — below is a working example you can refine):
    
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": [
            "ec2:DescribeInstances",
            "cloudwatch:GetMetricData",
            "cloudwatch:ListMetrics",
            "ce:GetCostAndUsage",
            "s3:GetBucketLocation",
            "s3:ListBucket"
          ],
          "Resource": "*"
        }
      ]
    }
    
    ```
    
- Attach this role to your EC2 instance (Actions → Security → Modify IAM role) or assign when launching. Using a role prevents embedding keys.

## **(Optional but recommended) Enable EC2 Detailed Monitoring**

- If you want 1-minute EC2 metrics, enable **Detailed monitoring** on the instance (EC2 Console → Instances → Actions → Monitor and troubleshoot → Enable detailed monitoring). Otherwise EC2 Basic is 5-minute resolution. (CloudWatch resolution rules apply). ([AWS Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html?utm_source=chatgpt.com))

## **Enable S3 CloudWatch Request Metrics (if you need 1-minute request metrics)**

- By default S3 **storage** metrics (BucketSizeBytes, NumberOfObjects) are provided daily and are free. If you need 1-minute request metrics (AllRequests, GetRequests, PutRequests, 4xx/5xx, BytesDownloaded/Uploaded) you must enable **CloudWatch request metrics / metric configuration** for the bucket (S3 Console → Bucket → Metrics tab → Request metrics → Create filter; name it (e.g. `EntireBucket`) and apply to desired objects). After enabling, S3 emits 1-minute metrics. ([AWS Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html?utm_source=chatgpt.com))

## **Security group / Network**

- Ensure outbound HTTPS (443) allowed from the EC2 instance so boto3 can call AWS APIs. (No public inbound access required for the script itself).

### **On the EC2 instance — install runtime & tools**

- Update and install Python:
    
    ```
    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip unzip curl
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip boto3
    
    ```
    
- (Optional) Install AWS CLI v2 to test credentials: `curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && sudo ./aws/install`

## **Quick pre-checks (run these before the script)**

- Confirm IAM role attached: `curl http://169.254.169.254/latest/meta-data/iam/info` (will show role info).
- Confirm you can run a benign API call: `aws cloudwatch list-metrics --namespace AWS/EC2 --region ap-south-1` (or use boto3 interactive). If this fails, check role permissions & network.

---

# 📂 Combined production-ready Python script (copy/paste; change the three placeholders only)

- Replace `INSTANCE_ID`, `REGION`, `BUCKET_NAME`.
- Do NOT paste access keys into this file. Use IAM role, or `aws configure` local credentials.

## **1. S3 *Idle Detection* Code (Ideal Code)**

This script only checks whether the S3 bucket is **idle or underutilized**.

Idle logic includes:

- Bucket size is very small
- Few objects
- Very low request activity
- No recent usage pattern

### **📌 s3_idle_check.py**


```
Paste the code that is provided
```

## **2. S3 *Usage Monitoring* Code (Usage Code)**

This script gives **detailed S3 usage analytics**, not just idle detection.

It includes:

- Bucket total size
- Object count
- AllRequests
- GetRequests
- PutRequests
- BytesUploaded
- BytesDownloaded
- 4xx & 5xx errors

**📌 s3_usage_monitor.py**

```
Paste the code that is provided
```

### 🚀 Output Examples

**Idle Code Output**

```
--- S3 Idle Check Report ---
Bucket: my-logs
Bucket Size (GB): 0.031
Object Count: 12
Requests (last 1 hr): 0

STATUS: Bucket appears idle / underutilized.

```

**Usage Code Output**

```
--- S3 Usage Monitoring Report ---
BucketSizeGB: 3.215
ObjectCount: 30521
AllRequests: 184
GetRequests: 162
PutRequests: 22
BytesDownloadedMB: 94.55
BytesUploadedMB: 12.44
4xxErrors: 0
5xxErrors: 0
```

---

# **📂 CloudWatch Dashboard Template for S3 (Copy–Paste JSON)**

This creates a full, clean, production-ready S3 dashboard showing:

✔ Bucket Size (GB)
✔ Number of Objects
✔ AllRequests
✔ GetRequests
✔ PutRequests
✔ BytesUploaded
✔ BytesDownloaded
✔ 4xxErrors
✔ 5xxErrors

All widgets use correct CloudWatch dimensions & metric types.

---

## 📌 **S3 CloudWatch Dashboard JSON Template**

Replace only:

```
YOUR_BUCKET_NAME
YOUR_REGION

```

Then create in CloudWatch → Dashboard → Actions → View/edit source → paste JSON.

---

```json
{
  "widgets": [
    {
      "type": "metric",
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [
            "AWS/S3",
            "BucketSizeBytes",
            "BucketName",
            "YOUR_BUCKET_NAME",
            "StorageType",
            "StandardStorage"
          ]
        ],
        "period": 86400,
        "stat": "Average",
        "region": "YOUR_REGION",
        "title": "S3 Bucket Size (GB)",
        "yAxis": {
          "left": {
            "label": "GB",
            "min": 0
          }
        },
        "transform": "value/1024/1024/1024"
      }
    },
    {
      "type": "metric",
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [
            "AWS/S3",
            "NumberOfObjects",
            "BucketName",
            "YOUR_BUCKET_NAME",
            "StorageType",
            "AllStorageTypes"
          ]
        ],
        "period": 86400,
        "stat": "Average",
        "region": "YOUR_REGION",
        "title": "Number of Objects in Bucket"
      }
    },
    {
      "type": "metric",
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [
            "AWS/S3",
            "AllRequests",
            "BucketName",
            "YOUR_BUCKET_NAME",
            "FilterId",
            "EntireBucket"
          ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "YOUR_REGION",
        "title": "All Requests (last hour)"
      }
    },
    {
      "type": "metric",
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [
            "AWS/S3",
            "GetRequests",
            "BucketName",
            "YOUR_BUCKET_NAME",
            "FilterId",
            "EntireBucket"
          ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "YOUR_REGION",
        "title": "GET Requests"
      }
    },
    {
      "type": "metric",
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [
            "AWS/S3",
            "PutRequests",
            "BucketName",
            "YOUR_BUCKET_NAME",
            "FilterId",
            "EntireBucket"
          ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "YOUR_REGION",
        "title": "PUT Requests"
      }
    },
    {
      "type": "metric",
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [
            "AWS/S3",
            "BytesUploaded",
            "BucketName",
            "YOUR_BUCKET_NAME",
            "FilterId",
            "EntireBucket"
          ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "YOUR_REGION",
        "title": "Bytes Uploaded (MB)",
        "transform": "value/1024/1024"
      }
    },
    {
      "type": "metric",
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [
            "AWS/S3",
            "BytesDownloaded",
            "BucketName",
            "YOUR_BUCKET_NAME",
            "FilterId",
            "EntireBucket"
          ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "YOUR_REGION",
        "title": "Bytes Downloaded (MB)",
        "transform": "value/1024/1024"
      }
    },
    {
      "type": "metric",
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [
            "AWS/S3",
            "4xxErrors",
            "BucketName",
            "YOUR_BUCKET_NAME",
            "FilterId",
            "EntireBucket"
          ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "YOUR_REGION",
        "title": "4xx Errors"
      }
    },
    {
      "type": "metric",
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [
            "AWS/S3",
            "5xxErrors",
            "BucketName",
            "YOUR_BUCKET_NAME",
            "FilterId",
            "EntireBucket"
          ]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "YOUR_REGION",
        "title": "5xx Errors"
      }
    }
  ]
}

```

---

## 🧭 **2. How to SEE & CHECK S3 metrics inside CloudWatch (Step-by-Step)**

To avoid confusion, here is the exact correct navigation path — 100% aligned with AWS UI.

---

### ⭐ **STEP 1 — Open CloudWatch**

1. Go to AWS Console
2. Search: **CloudWatch**
3. Open it

You'll land on **CloudWatch Home**.

---

### ⭐ **STEP 2 — Check S3 Storage Metrics**

These metrics update **every 24 hours**.

1. Left panel → **Metrics**
2. Choose **S3 Storage Metrics**
3. Select your bucket

You will now see:

- **BucketSizeBytes**
- **NumberOfObjects**

✔ These are available even if *request metrics* are NOT enabled
✔ But they refresh **once per day**, not every minute

---

### ⭐ **STEP 3 — Check S3 Request Metrics (must be enabled)**

These update **every 1 minute** once enabled.

1. Go to S3 Console
2. Select your bucket
3. Go to **Metrics** tab
4. Click **Request Metrics**
5. Enable:

```
EntireBucket (FilterId)

```

After ~5 minutes metrics will appear.

---

### ⭐ **STEP 4 — See Request Metrics in CloudWatch**

1. CloudWatch → **Metrics**
2. Choose **S3**
3. Select **Request Metrics**

Look for metrics:

- AllRequests
- GetRequests
- PutRequests
- BytesUploaded
- BytesDownloaded
- FirstByteLatency
- 4xxErrors
- 5xxErrors

Now click on them → graph appears.

---

### ⭐ **STEP 5 — Create Your Dashboard**

1. CloudWatch → **Dashboards**
2. Click **Create Dashboard**
3. Select **Line graph**
4. Add metric widgets:
    - BucketSizeBytes
    - NumberOfObjects
    - AllRequests
    - BytesUploaded
    - BytesDownloaded
    - Errors
5. Save dashboard

Your S3 monitoring screen is ready.

---

### ⭐ **STEP 6 — Validate the Data**

To confirm your S3 metrics are working:

### **A. Check if storage metrics show values**

- If everything shows **0**, you must wait 24 hours (S3 rule).

### **B. Check if request metrics show values**

Use this to generate activity:

```
aws s3 cp file.txt s3://your-bucket/
aws s3 ls s3://your-bucket/
aws s3 rm s3://your-bucket/file.txt

```

Go back to CloudWatch → you should see Get/Put requests.

---

### ⭐ **STEP 7 — Compare With Python Script Output**

Everything you see in CloudWatch will match the Python scripts I gave you:

| CloudWatch Metric | Python Script Output |
| --- | --- |
| BucketSizeBytes | Bucket Size (GB) |
| NumberOfObjects | Object Count |
| AllRequests | AllRequests |
| BytesDownloaded | BytesDownloadedMB |
| BytesUploaded | BytesUploadedMB |
| 4xxErrors | 4xxErrors |
| 5xxErrors | 5xxErrors |

---

Validation steps and how to avoid common failure points

• If CE API returns `DataUnavailable` or empty: confirm Cost Explorer is enabled in the Billing Console and that you are using the payer/management account for consolidated billing if applicable. ([AWS Documentation](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostAndUsage.html?utm_source=chatgpt.com))

• If S3 request metrics show zeros: confirm you created a metric configuration filter in the S3 Console (Metrics → Request metrics → Create filter named e.g. `EntireBucket`) and then generate some traffic — request metrics appear once metrics start arriving. Storage metrics are daily so they may be empty until AWS reports. ([AWS Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/configure-request-metrics-bucket.html?utm_source=chatgpt.com))

• If GetMetricData returns no datapoints for EC2: check whether the instance has **detailed monitoring** enabled for 1-min metrics, otherwise 5-min default applies. Also check your `StartTime`/`EndTime` window exactly matches the available data retention periods. ([AWS Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html?utm_source=chatgpt.com))

• Avoid `get_metric_statistics()` for multi-metric scripts — `GetMetricData` scales better and is the recommended API. (There have been vendor notices recommending migration; `GetMetricData` supports many more metrics per call). ([AWS Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_GetMetricData.html?utm_source=chatgpt.com))

---

Extra recommendations (production hardening)

1. **Use CloudWatch Alarms** for thresholds (CPU>xx, 5xxErrors>0) — so you get alerts instead of running scripts periodically.
2. **Send results to an S3/Glue/Datastore** if you want historical analytics beyond CloudWatch retention.
3. **Tagging**: ensure EC2 and S3 have cost allocation tags so Cost Explorer queries can be filtered by tag.
4. **Metric caching & retries**: add exponential backoff for API throttling (CloudWatch/CE have API rate limits).

---

Citations / Docs I used for the important rules above

- How to enable S3 Request Metrics (CloudWatch metrics configuration). ([AWS Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/configure-request-metrics-bucket.html?utm_source=chatgpt.com))
- S3 storage metrics (BucketSizeBytes, NumberOfObjects) are daily. ([AWS Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/metrics-dimensions.html?utm_source=chatgpt.com))
- CloudWatch GetMetricData API (better for large/multi metric queries). ([AWS Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_GetMetricData.html?utm_source=chatgpt.com))
- CloudWatch metric resolution and retention notes (periods: 1 min, 5 min, etc.). ([AWS Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_GetMetricStatistics.html?utm_source=chatgpt.com))
