
import os
import logging

from dotenv import load_dotenv
from groq import Groq, APIConnectionError, APIStatusError


load_dotenv()

logger = logging.getLogger(__name__)


class GroqService:

    def __init__(self):

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is missing in .env")

        self.primary_model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-120b"
        )

        self.fallback_model = os.getenv(
            "GROQ_FALLBACK_MODEL",
            "openai/gpt-oss-20b"
        )

        self.client = Groq(api_key=api_key)

    def _generate(
        self,
        model,
        question,
        context,
        conversation_history=None
    ):

        messages = [
            {
                "role": "system",
                "content": """
You are Knowledge AI, an intelligent document question-answering assistant.

CORE RULES:

1. Answer factual document questions using supplied document context.
2. Never invent facts, dates, numbers, policies or eligibility criteria.
3. If documents do not contain the answer, clearly say so.
4. Cite references like [1], [2], using only references provided in context.
5. Use previous conversation messages to understand follow-up questions.
6. Previous assistant answers are context, not verified evidence.
7. Verify factual claims against current retrieved document context.
8. Keep responses clear, structured and helpful.

LANGUAGE RULES:

- Follow explicitly requested language.
- Hindi questions should receive Hindi answers.
- English questions should receive English answers.
- Hinglish questions can receive Hinglish answers.
- Preserve technical terms when useful.
- Continue the requested language in follow-ups.

CONVERSATION RULES:

- Understand references such as "that", "those criteria",
  "reserved category", and "explain more" from conversation history.
- Do not repeat the entire previous answer unless requested.
- Answer the latest question directly.
- Ask for clarification when necessary.

GREETING RULES:

- Respond naturally to greetings such as hi, hello, hey,
  and good morning.
- Do not require document context for casual greetings.
- For unrelated questions, politely explain your document-assistant capabilities.
"""
            }
        ]

        # ADD CONVERSATION HISTORY

        if conversation_history:

            for message in conversation_history[-8:]:

                role = message.get("role")
                content = message.get("content", "")

                if role not in ("user", "assistant") or not content:
                    continue

                messages.append({
                    "role": role,
                    "content": content[:4000]
                })

        # CURRENT USER QUESTION

        messages.append({
            "role": "user",
            "content": f"""
RETRIEVED DOCUMENT CONTEXT:

{context}

LATEST USER QUESTION:

{question}

Answer the latest question using the supplied document context.
Use conversation history only to understand the user's intent.
"""
        })

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=1200
        )

        answer = response.choices[0].message.content

        if not answer:
            raise RuntimeError("Groq returned an empty response")

        return answer.strip()

    def generate_answer(
        self,
        question,
        context,
        conversation_history=None
    ):

        try:

            return self._generate(
                self.primary_model,
                question,
                context,
                conversation_history
            )

        except (APIConnectionError, APIStatusError) as error:

            status_code = getattr(error, "status_code", None)

            should_fallback = (
                isinstance(error, APIConnectionError)
                or status_code in (429, 500, 502, 503, 504)
            )

            if not should_fallback:
                raise

            logger.warning(
                "Primary Groq model failed. Trying fallback model: %s",
                self.fallback_model
            )

            if self.primary_model == self.fallback_model:
                raise

            return self._generate(
                self.fallback_model,
                question,
                context,
                conversation_history
            )
    