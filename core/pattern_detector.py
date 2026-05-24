import re


class PatternDetector:
    """
    Detects weaknesses and bad patterns in a password.
    Returns a list of weaknesses and a list of recommendations.
    """

    COMMON_PASSWORDS = set()  # loaded from file at startup

    def __init__(self, common_passwords_path: str = "data/common_passwords.txt"):
        self._load_common(common_passwords_path)

    def _load_common(self, path: str):
        try:
            with open(path, "r") as f:
                self.COMMON_PASSWORDS = set(
                    line.strip().lower() for line in f if line.strip()
                )
        except FileNotFoundError:
            self.COMMON_PASSWORDS = set()

    # ------------------------------------------------------------------ #

    def analyze(self, password: str) -> dict:
        """Returns weaknesses list and recommendations list."""
        if not password:
            return {"weaknesses": [], "recommendations": self._default_recs()}

        weaknesses = self._find_weaknesses(password)
        recommendations = self._build_recommendations(password, weaknesses)

        return {
            "weaknesses"      : weaknesses,
            "recommendations" : recommendations,
        }

    # ------------------------------------------------------------------ #

    def _find_weaknesses(self, password: str) -> list:
        weaknesses = []
        p = password.lower()

        if p in self.COMMON_PASSWORDS:
            weaknesses.append("⚠ This is one of the most commonly used passwords")

        if len(password) < 8:
            weaknesses.append("⚠ Too short — minimum 8 characters required")

        if not re.search(r'[A-Z]', password):
            weaknesses.append("⚠ No uppercase letters found")

        if not re.search(r'[a-z]', password):
            weaknesses.append("⚠ No lowercase letters found")

        if not re.search(r'[0-9]', password):
            weaknesses.append("⚠ No numbers found")

        if not re.search(r'[^a-zA-Z0-9]', password):
            weaknesses.append("⚠ No special characters (!@#$% etc.)")

        if re.search(r'(.)\1{2,}', password):
            weaknesses.append("⚠ Contains repeated characters (e.g. aaa, 111)")

        if re.search(r'(012|123|234|345|456|567|678|789|890)', p):
            weaknesses.append("⚠ Contains sequential numbers (e.g. 123, 456)")

        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', p):
            weaknesses.append("⚠ Contains sequential letters (e.g. abc, xyz)")

        keyboard_walks = ['qwerty', 'qwertyuiop', 'asdfgh', 'asdfghjkl',
                          'zxcvbn', 'zxcvbnm', 'qazwsx', 'qazwsxedc']
        if any(walk in p for walk in keyboard_walks):
            weaknesses.append("⚠ Contains keyboard pattern (e.g. qwerty, asdf)")

        if re.search(r'(password|passwd|pass|admin|login|welcome|user)', p):
            weaknesses.append("⚠ Contains common words (password, admin, etc.)")

        return weaknesses

    def _build_recommendations(self, password: str, weaknesses: list) -> list:
        recs = []
        p = password.lower()

        if len(password) < 12:
            recs.append("✔ Use at least 12 characters for better security")

        if not re.search(r'[A-Z]', password):
            recs.append("✔ Add uppercase letters (A–Z)")

        if not re.search(r'[a-z]', password):
            recs.append("✔ Add lowercase letters (a–z)")

        if not re.search(r'[0-9]', password):
            recs.append("✔ Include at least one number (0–9)")

        if not re.search(r'[^a-zA-Z0-9]', password):
            recs.append("✔ Add special characters like !@#$%^&*")

        if not weaknesses:
            recs.append("✔ Great password! Store it in a password manager")
            recs.append("✔ Never reuse this password on other accounts")
            recs.append("✔ Enable two-factor authentication (2FA) where possible")

        recs.append("✔ Avoid using personal info (name, birthday, etc.)")

        return recs

    def _default_recs(self) -> list:
        return [
            "✔ Use at least 12 characters",
            "✔ Mix uppercase, lowercase, numbers & symbols",
            "✔ Avoid common words or keyboard patterns",
            "✔ Use a password manager to store passwords safely",
        ]