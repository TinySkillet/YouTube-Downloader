import requests


def download_image(url, destination):
    
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful
  
    with open(destination, 'wb') as file:
        file.write(response.content)


if __name__ == "__main__":
    image_url = "https://i.ytimg.com/vi/lge7Rg5U-dk/sddefault.jpg?v=65a17a68"
    save_path = "thumbnail.jpg"

    download_image(image_url, save_path)
    print(f"Image downloaded and saved at: {save_path}")
