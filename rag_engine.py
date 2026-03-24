import ollama


def ask_llm(context_chunks, question):

    context = "\n\n".join(context_chunks)

    prompt = f"""
You are answering questions from a YouTube video.

Context:
{context}

Question:
{question}

Give a helpful answer.
"""

    response = ollama.chat(
        model="llama3",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response["message"]["content"]