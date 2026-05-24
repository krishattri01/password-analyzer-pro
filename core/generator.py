import secrets
import string


class PasswordGenerator:
    """
    Generates cryptographically secure random passwords.
    Uses Python's secrets module — much safer than random module.
    """

    def generate(self,
                 length: int = 16,
                 use_upper: bool = True,
                 use_lower: bool = True,
                 use_digits: bool = True,
                 use_special: bool = True) -> str:
        """
        Generates a password with guaranteed character type inclusion.
        Returns the generated password string.
        """
        # Build character pool based on user options
        pool = ""
        guaranteed = []  # ensures at least 1 of each selected type

        if use_lower:
            pool += string.ascii_lowercase
            guaranteed.append(secrets.choice(string.ascii_lowercase))

        if use_upper:
            pool += string.ascii_uppercase
            guaranteed.append(secrets.choice(string.ascii_uppercase))

        if use_digits:
            pool += string.digits
            guaranteed.append(secrets.choice(string.digits))

        if use_special:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            pool += special_chars
            guaranteed.append(secrets.choice(special_chars))

        if not pool:
            pool = string.ascii_letters + string.digits
            guaranteed = [secrets.choice(pool)]

        # Fill remaining length with random pool characters
        remaining_length = length - len(guaranteed)
        remaining = [secrets.choice(pool) for _ in range(remaining_length)]

        # Combine guaranteed + remaining, then shuffle so guaranteed
        # chars aren't always at the start
        password_chars = guaranteed + remaining
        secrets.SystemRandom().shuffle(password_chars)

        return "".join(password_chars)

    def generate_memorable(self, num_words: int = 4) -> str:
        """
        Generates a memorable passphrase using random words.
        Example: correct-horse-battery-staple style.
        """
        words = [
            "apple","river","stone","cloud","tiger","piano","storm",
            "flame","eagle","frost","globe","laser","maple","north",
            "ocean","pearl","quartz","raven","sigma","thunder","ultra",
            "viper","whale","xenon","yacht","zebra","amber","blaze",
            "coral","delta","ember","fable","giant","haven","ivory",
            "jewel","karma","lunar","magic","noble","orbit","prism"
        ]
        chosen = [secrets.choice(words) for _ in range(num_words)]
        number = secrets.randbelow(9000) + 1000   # 4-digit number
        special = secrets.choice("!@#$%&*")
        return "-".join(chosen) + str(number) + special