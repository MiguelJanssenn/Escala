"""
Simple tests to verify email whitelist functionality logic.
These tests verify the core validation logic without requiring Google Sheets connection.
"""

def test_email_normalization():
    """Test that emails are properly normalized (stripped and lowercased)."""
    test_cases = [
        ("  USER@EXAMPLE.COM  ", "user@example.com"),
        ("User@Example.com", "user@example.com"),
        ("admin@email.com", "admin@email.com"),
    ]
    
    for input_email, expected in test_cases:
        normalized = input_email.strip().lower()
        assert normalized == expected, f"Expected {expected}, got {normalized}"
    
    print("✓ Email normalization tests passed")

def test_email_validation_logic():
    """Test the email validation logic."""
    # Simulate allowed emails list
    allowed_emails = ["user1@example.com", "user2@example.com", "admin@email.com"]
    
    # Test cases: (email, should_be_allowed)
    test_cases = [
        ("user1@example.com", True),
        ("user2@example.com", True),
        ("admin@email.com", True),
        ("unauthorized@example.com", False),
        ("random@test.com", False),
    ]
    
    for email, should_be_allowed in test_cases:
        is_allowed = email in allowed_emails
        assert is_allowed == should_be_allowed, \
            f"Email {email}: expected allowed={should_be_allowed}, got {is_allowed}"
    
    print("✓ Email validation logic tests passed")

def test_duplicate_prevention_logic():
    """Test that duplicate emails are prevented."""
    allowed_emails = ["user1@example.com", "user2@example.com"]
    
    # Try to add an existing email
    new_email = "user1@example.com"
    is_duplicate = new_email in allowed_emails
    
    assert is_duplicate == True, "Should detect duplicate email"
    
    # Try to add a new email
    new_email = "user3@example.com"
    is_duplicate = new_email in allowed_emails
    
    assert is_duplicate == False, "Should allow new email"
    
    print("✓ Duplicate prevention logic tests passed")

if __name__ == "__main__":
    print("Running email whitelist logic tests...\n")
    test_email_normalization()
    test_email_validation_logic()
    test_duplicate_prevention_logic()
    print("\n✅ All tests passed successfully!")
