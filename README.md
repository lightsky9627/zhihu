# Zhihu Downloader (Dockerized)

A modern, web-based tool to download Zhihu articles and answers as Markdown, featuring a clean UI, visitor statistics, and an admin dashboard for centralized cookie management.

## Features

-   **Clean UI**: Simple interface to input URLs and optional custom cookies.
-   **Markdown Export**: Downloads content as a ZIP file containing the Markdown and assets.
-   **Smart Auth**: Uses user-provided cookie if available, falling back to a global admin-configured cookie.
-   **Visitor Stats**: Tracks daily/total visitors and downloads.
-   **Admin Dashboard**: secure area to manage the global cookie.
-   **Privacy**: Request logs are not persisted to disk.

## Installation & Deployment

### 1. Build Docker Image

```bash
docker build -t zhihu-downloader .
```

### 2. Run Container

```bash
docker run -d -p 5000:5000 --name zhihu-app zhihu-downloader
```

### 3. Access Application

-   **Home**: [http://localhost:5000](http://localhost:5000)
-   **Admin Login**: [http://localhost:5000/login](http://localhost:5000/login)

### 4. Admin Password

When the container starts, it generates a random admin password if one is not provided.
View the logs to get the password:

```bash
docker logs zhihu-app
```

Look for:
```
========================================
GENERATED ADMIN PASSWORD: xxxxxxxxxxxx
========================================
```

### Custom Password

To set a specific password, pass the `ADMIN_PASSWORD` environment variable:

```bash
docker run -d -p 5000:5000 -e ADMIN_PASSWORD=mysecretpassword zhihu-downloader
```

## Development

1.  Install dependencies: `pip install -r requirements.txt`
2.  Run Flask app: `python app.py`

## License

MIT
