---
trigger: always_on
---

Provide Context First: Always give the AI the product requirements before asking it to generate any code.

Inspect Before Modifying: Ask the AI to inspect existing files before it makes any changes to them.

Protect Working Code: Do not allow the AI to unnecessarily rewrite code that is already working.

Plan Large Changes: Ask for a step-by-step plan before making any large architectural changes.

Manual Reviews Required: You must manually review generated database relationships and all authentication/security code. Most importantly, do not blindly trust AI-generated database relationships or authentication logic.

Protect Secrets: Never expose .env secrets in your prompts or allow the AI to commit them.

Test After Changes: Ask the AI to run tests after any significant changes are made.

Commit Frequently: Use Git commits after each completed module to save your progress.

Isolate Changes: Keep frontend and backend changes separated whenever possible.

Question the AI: Ask the AI to explain any unexpected architectural changes before you accept them.

Work in Stages: Do not ask the AI IDE to generate the entire backend in one single prompt. Work in small, staged prompts (e.g., project structure first, then database models, then authentication, etc.).