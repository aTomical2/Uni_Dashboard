# **User and Book Service Deployment**  
### **Using Docker, RabbitMQ, and Kubernetes**

---

## **Overview**  
This project demonstrates a full-stack implementation of user and book services using Docker, RabbitMQ, and Kubernetes for microservice deployment and communication.  
The primary goal is to set up, test, and deploy services with asynchronous messaging and scalable architecture.

---

## **Features**  
- **User Service**: Allows CRUD operations for user data.  
- **Book Service**: Manages book-related data with CRUD operations.  
- **Asynchronous Messaging**: Uses RabbitMQ for service communication.  
- **Kubernetes Deployment**: Scalable deployment using Kubernetes with port forwarding for service accessibility.

---

## **Key Endpoints**  

### **User Service**  
| Endpoint              | Method | Description              |
|-----------------------|--------|--------------------------|
| `/users/add`          | POST   | Add a new user           |
| `/users/all`          | GET    | Retrieve all users       |
| `/users/<studentid>`  | GET    | Retrieve user by ID      |
| `/users/<studentid>`  | PUT    | Update user by ID        |
| `/users/<studentid>`  | DELETE | Delete user by ID        |

### **Book Service**  
| Endpoint              | Method | Description              |
|-----------------------|--------|--------------------------|
| `/books/add`          | POST   | Add a new book           |
| `/books/all`          | GET    | Retrieve all books       |
| `/books/<bookid>`     | GET    | Retrieve book by ID/ISBN |
| `/books/<bookid>`     | PUT    | Update book by ID/ISBN   |
| `/books/<bookid>`     | DELETE | Delete book by ID/ISBN   |

---

## **Setup Instructions**  

### **Prerequisites**  
Ensure the following tools are installed and configured:  
- Docker and Docker Compose  
- Kubernetes and `kubectl`  
- RabbitMQ and a PostgreSQL-compatible database  

### **Step 1: Build and Run Services with Docker**  

1. **Navigate to the `exercise_one` folder**  
   Ensure you are in the correct directory containing the service files.  

2. **Build and run the services**  
   Use the following command to build and start the services:  
   ```bash
   docker-compose up --build

3. **Test endpoints**
   Verify the services by testing the endpoints using curl or Postman.

---

### **Step 2: RabbitMQ Integration**

1. Duplicate the `exercise_one` folder to `exercise_two`.  
2. Configure RabbitMQ in the `docker_compose.yml` file.  
3. Update the services to connect to RabbitMQ and set environment variables for credentials.  
4. Run the updated services and verify the RabbitMQ message flow.  
   ```bash
    docker-compose up --build
---

### **Step 3: Kubernetes Deployment**

1. Convert the `docker_compose.yml` file to Kubernetes manifests using Kompose. Use Kompose to generate Kubernetes configuration files from the Docker Compose setup:  
   ```bash
   kompose convert
   
2. Deploy the services in Kubernetes. Apply the generated Kubernetes manifests to your cluster: 
   ```bash
   kubectl apply -f .
   
3. Set up port-forwarding for pods. Enable access to the services by forwarding the necessary ports from the pods to your local machine:
   ```bash
      kubectl port-forward <pod-name> <local-port>:<pod-port>
Replace &lt;pod-name&gt;, &lt;local-port&gt;, and &lt;pod-port&gt; with the corrected pod name and port numbers.  

4. Test the services. Verify the service endpoints using curl or Postman:
   ```bash
   curl http://localhost:<local-port>/<endpoint>
Replace <local-port> and <endpoint> with the respective port and endpoint being tested.

### **Author**
**Tom Gibson**
