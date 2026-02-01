"""
Text Sanitizer for TTS Output.

Cleans LLM output before sending to TTS to remove emojis, 
special characters, and formatting that would be spoken literally.
"""
import re

from loguru import logger
from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class TextSanitizerProcessor(FrameProcessor):
    """
    Sanitizes text frames before TTS processing.
    
    Removes:
    - Emojis and emoticons
    - Special characters that would be spoken literally
    - Markdown formatting (asterisks, underscores, etc.)
    - URLs
    - Excessive punctuation
    """
    
    # Emoji pattern - covers most Unicode emoji ranges
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
        "\U0001F680-\U0001F6FF"  # Transport and Map
        "\U0001F700-\U0001F77F"  # Alchemical Symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "\U0001F1E0-\U0001F1FF"  # Flags
        "]+",
        flags=re.UNICODE
    )
    
    # Common text emoticons
    EMOTICON_PATTERN = re.compile(
        r'(?:^|\s)'
        r'(?:'
        r'[:;=8xX][-\'^]?[)(\]\[dDpP/\\|@oO0*]'  # Standard emoticons like :) ;-) :D
        r'|[)(\]\[dDpP/\\|@oO0*][-\'^]?[:;=8xX]'  # Reversed emoticons like (: 
        r'|<3|</3'  # Hearts
        r'|\^_\^|\^-\^|-_-|T_T|O_O|o_o'  # Asian-style emoticons
        r'|:\'[\(\)]'  # Crying
        r'|\(y\)|\(n\)'  # Thumbs
        r')'
        r'(?:\s|$)',
        flags=re.IGNORECASE
    )
    
    # URL pattern
    URL_PATTERN = re.compile(
        r'https?://[^\s<>"{}|\\^`\[\]]+',
        flags=re.IGNORECASE
    )
    
    # Markdown formatting patterns
    MARKDOWN_PATTERNS = [
        (re.compile(r'\*\*([^*]+)\*\*'), r'\1'),  # Bold **text**
        (re.compile(r'\*([^*]+)\*'), r'\1'),       # Italic *text*
        (re.compile(r'__([^_]+)__'), r'\1'),       # Bold __text__
        (re.compile(r'_([^_]+)_'), r'\1'),         # Italic _text_
        (re.compile(r'~~([^~]+)~~'), r'\1'),       # Strikethrough ~~text~~
        (re.compile(r'`([^`]+)`'), r'\1'),         # Inline code `text`
        (re.compile(r'#{1,6}\s+'), ''),            # Headers # ## ###
        (re.compile(r'^\s*[-*+]\s+', re.MULTILINE), ''),  # List items
        (re.compile(r'^\s*\d+\.\s+', re.MULTILINE), ''),  # Numbered lists
        (re.compile(r'\[([^\]]+)\]\([^)]+\)'), r'\1'),    # Links [text](url)
    ]
    
    # Characters that might be spoken literally
    SPECIAL_CHARS = {
        '&': ' and ',
        '@': ' at ',
        '#': ' ',
        '$': ' dollars ',
        '%': ' percent ',
        '+': ' plus ',
        '=': ' equals ',
        '<': ' less than ',
        '>': ' greater than ',
        '|': ' ',
        '\\': ' ',
        '/': ' ',  # Remove slashes
        '~': ' ',
        '^': ' ',
        '{': ' ',
        '}': ' ',
        '[': ' ',
        ']': ' ',
        '*': ' ',  # Asterisks
        '_': ' ',  # Underscores when standalone
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info("TextSanitizerProcessor initialized")
    
    def sanitize_text(self, text: str) -> str:
        """
        Clean text for natural TTS output.
        
        Args:
            text: Raw text from LLM
            
        Returns:
            Cleaned text suitable for TTS
        """
        if not text:
            return text
        
        original = text
        
        # Remove emojis
        text = self.EMOJI_PATTERN.sub(' ', text)
        
        # Remove text emoticons
        text = self.EMOTICON_PATTERN.sub(' ', text)
        
        # Remove URLs
        text = self.URL_PATTERN.sub('', text)
        
        # Apply markdown cleaning
        for pattern, replacement in self.MARKDOWN_PATTERNS:
            text = pattern.sub(replacement, text)
        
        # Replace special characters
        for char, replacement in self.SPECIAL_CHARS.items():
            text = text.replace(char, replacement)
        
        # Clean up excessive punctuation (more than 2 in a row)
        text = re.sub(r'([!?.,])\1{2,}', r'\1\1', text)
        
        # Remove ellipsis spoken as "dot dot dot"
        text = re.sub(r'\.{3,}', '.', text)
        text = re.sub(r'…', '.', text)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Clean up spaces before punctuation
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        
        # Strip whitespace
        text = text.strip()
        
        if text != original:
            logger.debug(f"Sanitized text: '{original[:50]}...' -> '{text[:50]}...'")
        
        return text
    
    async def process_frame(
        self, frame: Frame, direction: FrameDirection
    ) -> None:
        """
        Process frames and sanitize text content.
        
        Args:
            frame: Input frame
            direction: Processing direction
        """
        await super().process_frame(frame, direction)
        
        # Only process text frames going downstream (to TTS)
        if direction == FrameDirection.DOWNSTREAM:
            if isinstance(frame, TextFrame):
                # Sanitize the text content
                sanitized = self.sanitize_text(frame.text)
                if sanitized:
                    # Push new frame with sanitized text
                    await self.push_frame(TextFrame(text=sanitized), direction)
                else:
                    # Skip empty frames after sanitization
                    logger.debug(f"Skipping empty frame after sanitization")
                return
        
        # Pass through all other frames unchanged
        await self.push_frame(frame, direction)
