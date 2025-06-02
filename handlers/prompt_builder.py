class PromptBuilder:
    @staticmethod
    def build(instruction, combined_context, recent_context, file_context, question):
        return (
            f"[System Instruction]\n"
            f"You are AI assistant with the following personality style:\n"
            f"{instruction}\n\n"
            f"[Conversation History]\n"
            f"{combined_context.strip() or 'No significant previous interactions.'}\n\n"
            f"[Recent Channel Messages]\n"
            f"{recent_context.strip() or 'No recent relevant messages.'}\n\n"
            f"[File Attachment Summary]\n"
            f"{file_context.strip() or 'No file uploaded.'}\n\n"
            f"[User Question]\n"
            f"{question.strip()}\n\n"
            f"[Expected Behavior]\n"
            f"Respond clearly and thoroughly, considering all the provided context and maintaining the defined personality style."
        )
