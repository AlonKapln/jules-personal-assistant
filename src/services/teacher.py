import logging
from src.config import config
from src.services.brain import brain

logger = logging.getLogger(__name__)

class Teacher:
    def __init__(self):
        pass

    def teach_english(self):
        """Generates an English lesson/fact based on settings."""
        try:
            level = config.get_setting("learning_level", "Intermediate")
            enabled = config.get_setting("learning_enabled", False)

            if not enabled:
                return None

            logger.info(f"Generating English lesson for level: {level}")

            context = f"""
            You are an English teacher. The user wants to learn English at an {level} level.

            Please provide a short, interesting English lesson.
            It could be:
            - A new vocabulary word with definition and example sentence.
            - An interesting idiom.
            - A grammar tip.
            - A fun fact about the language.

            Make it engaging and concise.
            """

            if brain.model:
                response = brain.model.generate_content(context)
                return f"🎓 **English Lesson**\n\n{response.text}"
            else:
                return None

        except Exception as e:
            logger.error(f"Error generating lesson: {e}", exc_info=True)
            return None

    def teach_word_of_the_day(self):
        """Generates a Word of the Day lesson."""
        try:
            level = config.get_setting("learning_level", "Intermediate")

            logger.info(f"Generating Word of the Day for level: {level}")

            context = f"""
            You are an English teacher. The user wants to learn English at an {level} level.

            Please provide a "Word of the Day".
            Format:
            **Word**: [The Word]
            **Pronunciation**: [IPA or phonetic]
            **Definition**: [Definition]
            **Example**: [Example sentence]
            **Fun Fact**: [Optional fun fact about the word]

            Keep it concise and formatted for a Telegram message.
            """

            if brain.model:
                response = brain.model.generate_content(context)
                return f"📖 **Word of the Day**\n\n{response.text}"
            else:
                return None
        except Exception as e:
            logger.error(f"Error generating Word of the Day: {e}", exc_info=True)
            return None

teacher = Teacher()
