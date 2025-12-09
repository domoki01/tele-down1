from setuptools import setup, find_packages

setup(
    name="download all",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "Flask==2.3.3",
        "pyTelegramBotAPI==4.14.0",
        "yt-dlp==2023.10.13",
        "requests==2.31.0",
        "gunicorn==20.1.0",
        "python-dotenv==1.0.0",
    ],
)
