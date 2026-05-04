# imgur-brute-crawler

A lightweight asynchronous crawler that fetches resources from Imgur, processes them through a pluggable architecture, and stores results locally or in Google Cloud Storage.

This project follows a layered architecture:

- `domain/` → Core models and interfaces
- `services/` → Orchestration logic (download, consumption, iteration)
- `infrastructure/` → Implementations of external systems (storage, HTTP, etc.)
- `scripts/` → CLI entrypoints

## Overview

The system is built around four main abstractions:

### Resource

The core entity in the system.

Any Imgur image (the main resource) can be retrieved by a link, such as [https://i.imgur.com/cGV1iV5.jpeg](https://i.imgur.com/cGV1iV5.jpeg).

That 7 character string, composed of letters (uppercase and lowercase) and digits (from 0 to 9), is the **ID of the resource**.

Note that a resource can be a JPEG (as seen above), a [PNG](https://i.imgur.com/ogHxQ5Y.png),
a [GIF](https://i.imgur.com/dzgsGOW.gif) or even a [MP4](https://i.imgur.com/f7DJByh_lq.mp4).
For the sake of simplicity, only JPEGs, PNGs and GIFs will be considered as resource in this project. 

Even if a image is a JPEG or a GIF, Imgur makes it accessible through a *.png* extension. If the final *.jpeg* or *.gif* is replaced with *.png*,
Imgur will redirect to the same image. We take advantage of that feature (or bug) such that a image can be found just by its ID.
So *.png* here is called the **raw extension of the resource**.

To validate its true extension, [file signatures](https://en.wikipedia.org/wiki/List_of_file_signatures) are checked: the first four bytes of
any image can tell if it's a JPEG, a PNG or a GIF. That would be called the **real extension of the resource**, or simply the resource extension.

Finally, after a resource is fetched, its bytes are downloaded, which are the **contents of the resource**.

### Downloader

An abstract service responsible for fetching a resource from Imgur by its ID.

It returns a resource if found or `None` if the resource does not exist.

A resource does not exist if trying to access its URL returns a _302 Found_ to [https://i.imgur.com/removed.png](https://i.imgur.com/removed.png).

> Implementations may include HTTP-based or API-based downloaders.

### Consumer

An abstract service responsible for handling the result of a download.

It's a callback that receives a resource ID if the resource does not exist or the resource itself otherwise.

> Implementations may include storing to disk or cloud storage, logging results or forwarding to another pipeline.

### ID iterator

An abstract service responsible for providing a stream of IDs to crawl.

> Implementations may include generating random IDs, reading from a file or from a in-memory iterator.

---

The general execution flow is:

1. `IdIterator` yields an `id`
2. `Downloader.download(id)` is called
3. If resource exists, `Consumer.consume_hit(resource)`
4. If resource does not exist, `Consumer.consume_miss(id)`
5. Repeat until iterator is exhausted
6. Close iterator

## Installation

It's recommended to have [Poetry](https://python-poetry.org) in your machine.

1. Clone the repository:

```shell
git clone https://github.com/ezgrs/imgur-brute-crawler
cd imgur-brute-crawler
```

2. Install the dependencies:

```shell
poetry install
```

3. If you don't plan to use Google Cloud Storage, skip to step 8.

4. Check if you have the [Google Cloud SDK](https://docs.cloud.google.com/sdk/docs/install-sdk) installed:

```shell
gcloud --version
```
```no-lang
Google Cloud SDK 565.0.0
beta 2026.04.10
bq 2.1.31
core 2026.04.10
gcloud-crc32c 1.0.0
gsutil 5.3
```

5. Log in into your Google Cloud account:

```shell
gcloud auth login
```

This command will first open your browser to the sign-in page where you complete authentication.

Then it'll show your current list of projects: choose which one you would like to use its Storage.

> Running this will allow **you** to run `gcloud` commands from your terminal, finding your credentials automatically.

6. Create your Application Default Credentials (ADC) file:

```shell
gcloud auth application-default login
```

> Running this will allow **your SDK library** to run the SDK code, finding your credentials automatically.

7. If your project is not already set for some reason, you can do so by running:

```shell
gcloud config set project YOUR_PROJECT_ID
```

## Usage

### CLI

The crawler is configured via CLI arguments:

```shell
poetry run python -m imgurbc.scripts.crawler
```

| Flag                               | Description                                          |
| ---------------------------------- | ---------------------------------------------------- |
| `-d`, `--delay`                    | Delay between requests in seconds (default: 1)       |
| `--gcloud-storage-bucket-name`     | GCS bucket name (optional)                           |
| `--gcloud-storage-bucket-location` | GCS bucket location (default: us-east1)              |
| `-i`, `--input`                    | Input IDs (optional, strings)                        |
| `--no-stdout`                      | Disable stdout logging                               |
| `-o`, `--output`                   | Local directory to store the images found            |

Note that

- If `--delay` is 0, Imgur may rate-limit the connection
- If `--gcloud-storage-bucket-name` is not given, no Cloud access will be made
- `--gcloud-storage-bucket-location` is only applied if `--gcloud-storage-bucket-name` is given and if its bucket does not already exist inside the Google Cloud project's Storage  
- If `--input` is not given, a infinite random stream of IDs will be tried instead
- If `--output` is not given, images found will be discarded
- You can use both `--gcloud-storage-bucket-name` and `--output`, saving images both locally and to the cloud

#### Examples

If you want to download a known set of images and save it to the `output` directory:

```shell
poetry run python -m imgurbc.scripts.crawler -i dzgsGOW ogHxQ5Y cGV1iV5 -o ./output
```

If you want to download a random set of images and save it to Google Cloud Storage:

```shell
poetry run python -m imgurbc.scripts.crawler --gcloud-storage-bucket-name my-bucket
```


### Google Cloud

1. If you already have a service account, skip to step 3.

2. Create a service account to upload the images to the specified bucket:

```shell
gcloud iam service-accounts create SERVICE_ACCOUNT_NAME
```

3. If your service account already has storage permissions, skip to step 5.

4. Give the service account permission to upload images to the bucket:

```shell
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_NAME@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

5. Deploy the API to Google Cloud Run:

```shell
gcloud run deploy CLOUD_FUNCTION_NAME \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --service-account=SERVICE_ACCOUNT_NAME@PROJECT_ID.iam.gserviceaccount.com
```

This will deploy a FastAPI application with a single endpoint, `POST /imgur`, which receives
a `imgur_id` in its body and saves it to Google Cloud Storage if it exists. It always returns
_200 OK_.

### Google Cloud with GitHub

Considering you have a GitHub repository `https://github.com/YOUR_GITHUB_USER/YOUR_REPO`,
you can set up a service account to deploy the Cloud Run service whenever you do a push.

Check out the workflow file at _.github/workflows/cloud-run-deploy.yml_.

1. Enable the IAM Service Account Credentials API:

```shell
gcloud services enable iamcredentials.googleapis.com --project PROJECT_ID
```
```langnone
Operation "operations/XXXX.X9-9999999999999-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" finished successfully.
```

2. Create a Workload Identity pool:

```shell
gcloud iam workload-identity-pools create github-pool
  --project=PROJECT_ID
  --location=global
  --display-name="GitHub Pool"
```
```langnone
Created workload identity pool [github-pool].
```

3. Create a GitHub OIDC provider:

```shell
gcloud iam workload-identity-pools providers create-oidc github-provider 
  --project=PROJECT_ID
  --location=global 
  --workload-identity-pool=github-pool
  --display-name="GitHub Provider"
  --issuer-uri="https://token.actions.githubusercontent.com"
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository"
  --attribute-condition="assertion.repository=='YOUR_GITHUB_USER/YOUR_REPO'"
```
```langnone
Created workload identity pool provider [github-provider].
```

4. Query the provider resource name:

```shell
gcloud iam workload-identity-pools providers describe github-provider
  --project=PROJECT_ID
  --location=global
  --workload-identity-pool=github-pool
  --format="value(name)"
```
```langnone
projects/9999999999999/locations/global/workloadIdentityPools/github-pool/providers/github-provider
```

The 13-digit string will be refered as the `PROJECT_NUMBER`. 

5. Create a service account to execute the deploy:

```shell
gcloud iam service-accounts create github-deployer
```
```langnone
Created service account [github-deployer].
```

Add the following roles:

- `run.admin` (gives full control over Cloud Run services)
- `iam.serviceAccountUser` (allows GitHub to use a service account when deploying)
- `artifactregistry.writer` (allows pushing build artifacts)
- `cloudbuild.builds.editor` (allows Cloud Build to run builds)
- `storage.objectAdmin` (gives full control over objects inside Cloud Storage buckets)
- `storage.bucketViewer` (allows reading Cloud Storage bucket metadata)

For instance,

```shell
gcloud projects add-iam-policy-binding PROJECT_ID
  --member="serviceAccount:github-deployer@PROJECT_ID.iam.gserviceaccount.com"
  --role="roles/ROLE_NAME"
```
```langnone
Updated IAM policy for project [PROJECT_ID].
```

Also link the service account to the GitHub provider:

```shell
gcloud iam service-accounts add-iam-policy-binding
  github-deployer@PROJECT_ID.iam.gserviceaccount.com
  --project=PROJECT_ID
  --role="roles/iam.serviceAccountTokenCreator"
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_USER/YOUR_REPO"
```
```langnone
Updated IAM policy for serviceAccount [github-deployer@PROJECT_ID.iam.gserviceaccount.com].
```

