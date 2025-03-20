with open("static/assets/image copy.png", "rb") as file:
    binary_data = file.read()
    hex_data = binary_data.hex()
    print(hex_data)
