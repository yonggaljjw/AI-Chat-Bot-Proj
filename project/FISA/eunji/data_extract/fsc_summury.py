from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration

# Load Model and Tokenizer
tokenizer = PreTrainedTokenizerFast.from_pretrained("EbanLee/kobart-summary-v3")
model = BartForConditionalGeneration.from_pretrained("EbanLee/kobart-summary-v3")

# Encoding
df = pd.read_csv("./fsc_announcements_extract.csv")

input_text = df['주요내용'][0]
inputs = tokenizer(input_text, return_tensors="pt", padding="max_length", truncation=True, max_length=1026)

# Generate Summary Text Ids
summary_text_ids = model.generate(
    input_ids=inputs['input_ids'],
    attention_mask=inputs['attention_mask'],
    bos_token_id=model.config.bos_token_id,
    eos_token_id=model.config.eos_token_id,
    length_penalty=1.0,
    max_length=300,
    min_length=12,
    num_beams=6,
    repetition_penalty=1.5,
    no_repeat_ngram_size=15,
    )

# Decoding Text Ids
print(input_text)
print('---')
print(tokenizer.decode(summary_text_ids[0], skip_special_tokens=True))
