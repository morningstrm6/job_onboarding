import os
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load local .env (ignored in git)
load_dotenv()

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    ASK_NAME,
    ASK_GENDER,
    ASK_PHONE,
    ASK_EMAIL,
    ASK_WHATSAPP,
    ASK_TELE_ID,
    ASK_ACCOUNT,   # new
    ASK_IFSC,      # new
    ASK_BANK,
    CONFIRM,
) = range(10)

# Env vars (must be set in runner or local .env)
BOT_TOKEN = os.getenv("BOT_TOKEN")
HR_TELEGRAM_USERNAME = os.getenv("HR_TELEGRAM_USERNAME")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
ONBOARDING_IMAGE_URL = os.getenv("ONBOARDING_IMAGE_URL")
GOOGLE_CREDS_JSON_CONTENT = os.getenv("GOOGLE_CREDS_JSON_CONTENT")

# Safety checks
if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set. Exiting.")
    raise SystemExit("BOT_TOKEN not set")
if not SPREADSHEET_ID:
    logger.error("SPREADSHEET_ID is not set. Exiting.")
    raise SystemExit("SPREADSHEET_ID not set")
if not GOOGLE_CREDS_JSON_CONTENT:
    logger.error("GOOGLE_CREDS_JSON_CONTENT is not set. Exiting.")
    raise SystemExit("GOOGLE_CREDS_JSON_CONTENT not set")

# Write service account content to a temp file
GOOGLE_CREDS_JSON_PATH = "/tmp/service_account.json"
with open(GOOGLE_CREDS_JSON_PATH, "w") as f:
    f.write(GOOGLE_CREDS_JSON_JSON_CONTENT)

# Google Sheets helper
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(
        GOOGLE_CREDS_JSON_PATH, scopes=scopes
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    return sh.sheet1

# Utils
def generate_emp_code(phone: str) -> str:
    digits = "".join([c for c in phone if c.isdigit()])
    last4 = digits[-4:] if len(digits) >= 4 else digits.zfill(4)
    return f"CHEGG{last4}"

def is_valid_phone(phone: str) -> bool:
    digits = "".join([c for c in phone if c.isdigit()])
    return len(digits) >= 7

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["collected"] = {}
    await update.message.reply_text(
        "Welcome to the Onboarding Bot! Let's start with a few questions.\n\n"
        "First — what's your full name?"
    )
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["collected"]["name"] = name
    kb = ReplyKeyboardMarkup(
        [["Male", "Female", "Other"]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    await update.message.reply_text(
        "What's your gender?", reply_markup=kb
    )
    return ASK_GENDER

async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gender = update.message.text.strip()
    context.user_data["collected"]["gender"] = gender
    await update.message.reply_text(
        "Please enter your Phone Number (digits only, e.g. 9876543210)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not is_valid_phone(phone):
        await update.message.reply_text(
            "That doesn't look like a valid phone number. "
            "Please send digits (e.g. 9876543210)."
        )
        return ASK_PHONE
    context.user_data["collected"]["phone"] = phone
    await update.message.reply_text("Please enter your Email address:")
    return ASK_EMAIL

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    context.user_data["collected"]["email"] = email
    await update.message.reply_text(
        "Please enter your WhatsApp Number (or type 'same' if it's same as phone):"
    )
    return ASK_WHATSAPP

async def ask_whatsapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    whats = update.message.text.strip()
    if whats.lower() == "same":
        whats = context.user_data["collected"].get("phone", "")
    context.user_data["collected"]["whatsapp"] = whats
    await update.message.reply_text(
        "Please send your Telegram UserId (or username). "
        "Example: @username or numeric id:"
    )
    return ASK_TELE_ID

async def ask_tele_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tele = update.message.text.strip()
    context.user_data["collected"]["telegram_user"] = tele

async def ask_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    acct = update.message.text.strip()
    context.user_data['collected']['account_number'] = acct
    await update.message.reply_text(
        "Please enter your bank IFSC code (e.g., HDFC0001234):"
    )
    return ASK_IFSC

async def ask_ifsc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ifsc = update.message.text.strip().upper()
    context.user_data['collected']['ifsc'] = ifsc
    await update.message.reply_text("Please enter your Bank Name:")
    return ASK_BANK

async def ask_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank = update.message.text.strip()
    context.user_data['collected']['bank_name'] = bank
    c = context.user_data["collected"]
    summary = (
        "Thanks — here's the summary of what you entered:\n\n"
        f"Name: {c.get('name')}\n"
        f"Gender: {c.get('gender')}\n"
        f"Phone: {c.get('phone')}\n"
        f"Email: {c.get('email')}\n"
        f"WhatsApp: {c.get('whatsapp')}\n"
        f"Telegram: {c.get('telegram_user')}\n\n"
        f"Account Number: {c.get('account_number')}\n"
        f"IFSC: {c.get('ifsc')}\n"
        f"Bank Name: {c.get('bank_name')}\n\n"
        "Send 'confirm' to submit or 'cancel' to abort."
    )
    await update.message.reply_text(summary)
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip().lower()
    if txt not in ("confirm", "yes"):
        await update.message.reply_text(
            "Onboarding canceled. If you'd like to start again, send /start."
        )
        return ConversationHandler.END

    c = context.user_data["collected"]
    emp_code = generate_emp_code(c.get("phone", ""))
    c["employee_code"] = emp_code
    c["created_at"] = datetime.utcnow().isoformat()

    # Save to Google Sheet (with header creation if needed)
    try:
        sheet = get_sheet()
        header = [
            "Employee Code", "Name", "Gender", "Phone", "Email",
            "WhatsApp", "Telegram User",
            "Account Number", "IFSC", "Bank Name",
            "Timestamp"
        ]
        existing = sheet.row_values(1)
        if not existing or existing[0] != "Employee Code":
            sheet.insert_row(header, index=1)
        row = [
            c.get('employee_code'),
            c.get('name'),
            c.get('gender'),
            c.get('phone'),
            c.get('email'),
            c.get('whatsapp'),
            c.get('telegram_user'),
            c.get('account_number', ''),
            c.get('ifsc', ''),
            c.get('bank_name', ''),
            c.get('created_at'),
        ]
        sheet.append_row(row)
    except Exception:
        logger.exception("Failed to write to Google Sheet")
        await update.message.reply_text(
            "Sorry — there was an error saving your details. "
            "Please try again later."
        )
        return ConversationHandler.END

    hr_link = (
        f"https://t.me/{HR_TELEGRAM_USERNAME}"
        if HR_TELEGRAM_USERNAME else "HR contact not configured."
    )
    await update.message.reply_text(
        f"Your Employee Code: *{emp_code}*", parse_mode="Markdown"
    )
    if ONBOARDING_IMAGE_URL:
        try:
            await update.message.reply_photo(photo=ONBOARDING_IMAGE_URL)
        except Exception:
            await update.message.reply_text(
                "(Could not send image — please contact HR.)"
            )
    instruction = (
        "**Next step — share your Employee Code with HR**\n\n"
        "Please share your *Employee Code* with HR to complete the onboarding process. "
        "Once HR confirms the code, your onboarding will be finalized and you will "
        "receive further instructions and access details."
    )
    await update.message.reply_text(instruction, parse_mode="Markdown")
    if HR_TELEGRAM_USERNAME:
        await update.message.reply_text(
            f"Contact HR here: {hr_link}\n\nThank you — your details have been submitted."
        )
    else:
        await update.message.reply_text(
            "HR contact is not configured. Please contact your HR team directly."
        )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Onboarding canceled. If you'd like to start again, send /start.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
# Build app
app = ApplicationBuilder().token(BOT_TOKEN).build()
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
        ASK_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gender)],
        ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
        ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
        ASK_WHATSAPP: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_whatsapp)],
        ASK_TELE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_tele_id)],
        ASK_ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_account)],
        ASK_IFSC: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ifsc)],
        ASK_BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_bank)],
        CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True,
)
app.add_handler(conv_handler)

if __name__ == "__main__":
    logger.info("Bot started in polling mode...")
    app.run_polling()