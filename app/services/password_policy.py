MIN_LENGTH = 8


def validate_password(password):
    issues = []

    if len(password) < MIN_LENGTH:
        issues.append(f"at least {MIN_LENGTH} characters")
    if not any(c.isupper() for c in password):
        issues.append("an uppercase letter")
    if not any(c.islower() for c in password):
        issues.append("a lowercase letter")
    if not any(c.isdigit() for c in password):
        issues.append("a digit")

    return issues


def password_strength(password):
    if not password:
        return "empty"

    if validate_password(password):
        return "weak"

    return "strong" if len(password) >= 12 else "medium"
