from transformers import PreTrainedTokenizerFast, BartForConditionalGeneration
#  Load Model and Tokenize
tokenizer = PreTrainedTokenizerFast.from_pretrained("ainize/kobart-news")
model = BartForConditionalGeneration.from_pretrained("ainize/kobart-news")
# Encode Input Text
input_text = "개정이유를 찾을 수 없습니다. 가. 연구·개발 목적으로 망분리 규제 예외 적용시 가명처리된 개인신용정보 활용을 허용(안 제15조제1항제3호 및 제5호) 나. 클라우드컴퓨팅서비스 위수탁 계약서 주요 기재사항 중 기본포함 사항 간소화(안 별표2의5)"
input_ids = tokenizer.encode(input_text, return_tensors="pt")
# Generate Summary Text Ids
summary_text_ids = model.generate(
    input_ids=input_ids,
    bos_token_id=model.config.bos_token_id,
    eos_token_id=model.config.eos_token_id,
    length_penalty=2.0,
    max_length=142,
    min_length=56,
    num_beams=4,
)
# Decoding Text
print(tokenizer.decode(summary_text_ids[0], skip_special_tokens=True))