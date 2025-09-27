# Extract all tokens from linguistic processing data
# Input: JSON object with linguistic processing results
# Output: String with one token per line

(.sents // [])[]
| select(.lg == env.LANGUAGE)
| ((.tokens // .tok) // [])[]
| .t
