# Pulse — Social Media Platform 

Pulse is a full-stack social media web application built with Django, designed to simulate the core functionalities of modern social platforms. It allows users to create content, connect with others, and engage through a dynamic and interactive system backed by a scalable REST API.

The project focuses on clean architecture, secure authentication, and real-world backend practices, making it suitable as both a learning project and a portfolio-ready application.

## Features

Pulse provides a complete set of social networking functionalities:

* **Authentication System (JWT-based)**
  Secure user authentication using JSON Web Tokens, including registration, login, and logout.

* **User Relationships (Follow System)**
  Users can follow and unfollow others, enabling a personalized content feed and social graph structure.

* **Post Creation and Management**
  Authenticated users can create, update, and delete posts.

* **Social Interactions**
  Users can interact with posts through likes and comments.

* **Notification System**
  A dynamic notification system powered by Django signals that triggers events such as new followers and interactions.

* **Media Handling**
  Support for profile pictures and post images.

* **RESTful API**
  API built with Django REST Framework for scalability and integration with future frontends.

## Architecture

The application follows a modular architecture:

* `users`: user management and authentication
* `posts`: post logic and interactions
* `notifications`: event-driven notifications

This structure improves scalability, maintainability, and separation of concerns.

## Technologies

* Python 3.11
* Django 5
* Django REST Framework
* SimpleJWT
* PostgreSQL
* Docker
* Gunicorn


## Deployment

The application is deployed on Render using Docker for containerization. Both the web service and the PostgreSQL database are hosted on Render, providing a fully cloud-based infrastructure with persistent storage and scalable deployment.








---

