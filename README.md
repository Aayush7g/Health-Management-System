# Health Management System

A comprehensive web application designed to streamline healthcare services, enabling efficient management of patient appointments, medical records, and more.

## Features

- **Patient Portal:** Patients can book appointments, view medical records, and access personalized health insights.
- **Doctor Portal:** Doctors can manage appointments, update patient records, and utilize AI-driven tools for enhanced diagnostics.
- **AI-Driven Health Assistant:** An integrated chatbot offering personalized health insights and interactive support.

## AI-Driven Health Assistant Integration

We've integrated an advanced AI-driven health assistant to enhance patient engagement and provide personalized health insights. This assistant offers:

- **Personalized Medical Insights:** Fetches patient details to provide tailored recommendations.
- **AI Health Chatbot:** Facilitates natural language interaction for health-related queries.
- **Data-Driven Predictions:** Utilizes patient history for better analysis.
- **Interactive UI:** Powered by Streamlit for a seamless experience.

For more details, visit the [AI-driven health assistant repository](https://github.com/TechieSoham/AI-driven-health-assistant).

## Technologies Used

- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, Bootstrap
- **Database:** MySQL
- **APIs:** Twitter OAuth for authentication, Overpass API for hospital data
- **Mapping:** Leaflet.js for interactive maps
- **AI Integration:** Streamlit, LangChain, Ollama

## Installation

Follow these steps to set up the project locally.

### Prerequisites

- Python 3.x
- MySQL
- Git

### Steps

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your-username/health-management-system.git
   cd health-management-system

2. **Set Up a Virtual Environment:**
    ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

3. **Install Dependencies:**
   ```bash
   pip install Flask mysql-connector-python requests-oauthlib python-dotenv

4. **Configure the Database:**
    ```bash
   DATABASE_USER=your_username
   DATABASE_PASSWORD=your_password
   DATABASE_HOST=localhost
   DATABASE_NAME=your_database

###Contributing
We welcome contributions to enhance the functionality of this system. Please fork the repository and submit a pull request for any improvements.

    



