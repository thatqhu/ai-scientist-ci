class Utils:
    @staticmethod
    def extract_json_from_response(response_content: str) -> str:
        """
        Extract JSON from LLM response, handling markdown code blocks.

        Args:
            response_content: Raw LLM response (may contain ```json ... ```)

        Returns:
            Clean JSON string
        """
        import re

        content = response_content.strip()

        # Try to extract from markdown code block
        # Pattern matches ```json ... ``` or ``` ... ```
        code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        matches = re.findall(code_block_pattern, content)

        if matches:
            # Use the first code block found
            content = matches[0].strip()

        # Remove any leading/trailing whitespace or newlines
        content = content.strip()

        # If content doesn't start with { or [, try to find JSON object
        if not content.startswith(('{' , '[')):
            # Try to find JSON object in the content
            json_start = content.find('{')
            if json_start != -1:
                # Find matching closing brace
                brace_count = 0
                for i, char in enumerate(content[json_start:], json_start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            content = content[json_start:i+1]
                            break

        return content
