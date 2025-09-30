def to_json(lst):
    dct = {"needs": lst[0]}
    dct["text"] = lst[1]
    dct["hashtags"] = lst[2].split(" ")
    dct["url"] = lst[3]
    return dct


def to_text(dct):
    text = f"{dct['needs']}\n"

    text += dct["text"] + "\n\n"
    text += " ".join(dct["hashtags"]) + "\n"
    # Add direct message link if message_id exists
    if "message_id" in dct and dct["message_id"]:
        message_url = f"https://t.me/UstozShogird/{dct['message_id']}"
        text += f"__👉__ [@UstozShogird kanaliga ulanish]({message_url})\n"
    else:
        text += dct["url"] + "\n"

    return text


def clean_markdown_for_telegram(text):
    """Clean and fix Markdown formatting for Telegram."""
    import re

    try:
        # Fix double asterisks (bold) - convert to single asterisks for Telegram
        text = re.sub(r"\*\*(.*?)\*\*", r"*\1*", text)

        # Fix double underscores (italic) - convert to underscores for Telegram
        text = re.sub(r"__(.*?)__", r"_\1_", text)

        # KEEP markdown links intact - DON'T remove [text](url) format
        # Just ensure they are properly formatted for Telegram

        # Handle unclosed markdown - remove orphaned * and _
        # But be careful not to remove * and _ that are part of links

        # Count asterisks outside of links
        text_without_links = re.sub(r"\[([^\]]+)\]\([^)]+\)", "", text)
        asterisk_count = text_without_links.count("*")
        if asterisk_count % 2 != 0:
            # Find last asterisk that's not part of a link and remove it
            parts = text.split("[")
            if len(parts) > 1:
                # Only clean asterisks in the first part (before any links)
                parts[0] = re.sub(r"\*(?![^[]*\])", "", parts[0], count=1)
                text = "[".join(parts)
            else:
                last_asterisk = text.rfind("*")
                if last_asterisk != -1:
                    text = text[:last_asterisk] + text[last_asterisk + 1 :]

        # Count underscores outside of links
        underscore_count = text_without_links.count("_")
        if underscore_count % 2 != 0:
            # Find last underscore that's not part of a link and remove it
            parts = text.split("[")
            if len(parts) > 1:
                # Only clean underscores in the first part (before any links)
                parts[0] = re.sub(r"_(?![^[]*\])", "", parts[0], count=1)
                text = "[".join(parts)
            else:
                last_underscore = text.rfind("_")
                if last_underscore != -1:
                    text = text[:last_underscore] + text[last_underscore + 1 :]

        # Remove problematic characters but preserve link structure
        text = text.replace("`", "'")
        # Don't remove pipes that might be in URLs

        return text
    except Exception:
        # If markdown cleaning fails, return plain text without any formatting
        return remove_all_markdown(text)


def remove_all_markdown(text):
    """Remove all markdown formatting as a fallback."""
    import re

    # Remove all markdown formatting
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Remove ** bold **
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # Remove * italic *
    text = re.sub(r"__(.*?)__", r"\1", text)  # Remove __ italic __
    text = re.sub(r"_(.*?)_", r"\1", text)  # Remove _ italic _
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # Remove links
    text = re.sub(r"`([^`]+)`", r"\1", text)  # Remove inline code

    return text
