import requests
import json

BASE_URL = "http://localhost:5008"

def test_borrow_service():
    # Test valid borrow request
    print("1. Testing valid borrow request...")
    response = requests.post(
        f"{BASE_URL}/borrow",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"studentid": "S10001", "bookid": "B10001"}),
    )
    print(f"Status Code: {response.status_code}, Response: {response.json()}")
    assert response.status_code == 201, "Failed: Valid borrow request should succeed."

    # Test invalid student_id
    print("\n2. Testing invalid student_id...")
    response = requests.post(
        f"{BASE_URL}/borrow",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"studentid": "InvalidStudent", "bookid": "B10002"}),
    )
    print(f"Status Code: {response.status_code}, Response: {response.json()}")
    assert response.status_code == 404, "Failed: Borrow request with invalid student_id should return 404."

    # Test invalid book_id
    print("\n3. Testing invalid book_id...")
    response = requests.post(
        f"{BASE_URL}/borrow",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"studentid": "S10001", "bookid": "InvalidBook"}),
    )
    print(f"Status Code: {response.status_code}, Response: {response.json()}")
    assert response.status_code == 404, "Failed: Borrow request with invalid book_id should return 404."

    # Borrow 5 books for a student
    print("\n4. Borrowing 5 books for a student...")
    for i in range(2, 7):
        response = requests.post(
            f"{BASE_URL}/borrow",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"studentid": "S10001", "bookid": f"B1000{i}"}),
        )
        print(f"Borrowing Book {i}: Status Code: {response.status_code}, Response: {response.json()}")
        assert response.status_code == 201, f"Failed: Borrow request for book {i} should succeed."

    # Test borrowing more than 5 books
    print("\n5. Testing borrowing more than 5 books...")
    response = requests.post(
        f"{BASE_URL}/borrow",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"studentid": "S10001", "bookid": "B10007"}),
    )
    print(f"Status Code: {response.status_code}, Response: {response.json()}")
    assert response.status_code == 400, "Failed: Borrowing more than 5 books should return 400."

    # Verify list of borrowed books
    print("\n6. Verifying borrowed books for the student...")
    response = requests.get(f"{BASE_URL}/borrows/S10001")
    print(f"Status Code: {response.status_code}, Response: {response.json()}")
    assert response.status_code == 200, "Failed: Fetching borrowed books should succeed."
    borrowed_books = response.json()
    assert len(borrowed_books) == 5, "Failed: Student should have exactly 5 borrowed books."
    print("Borrowed books verified successfully!")

if __name__ == "__main__":
    test_borrow_service()
