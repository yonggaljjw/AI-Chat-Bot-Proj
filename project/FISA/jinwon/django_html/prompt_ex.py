    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": """You are a highly assistant that analyzes financial data based on the given DataFrame \n
            The answer should provide a summarized analysis and insights"""},
            {"role": "user", "content": f"financial dataframe: {df}"},
            {"role": "assistant", "content" : 
            """Analyze the following financial data for a company and provide insights. Focus on:
            1. Balance Sheet Analysis:
            - Changes in equity: common stock, retained earnings, total equity.
            2. Income Statement Analysis:
            - Changes in sales revenue and operating profit.
            - Changes in net income.
            3. Cash Flow Analysis:
            - Changes in current assets and liabilities.
            - Liquidity analysis.
            4. Profitability and Performance Analysis:
            - Operating profit and net income.
            - Current vs. previous period profitability.
            5. Financial Health Analysis:
            - Total assets, liabilities, and equity.
            - Current vs. previous period comparison."""}
        ],
        max_tokens=1000, # 비용 발생하므로 시도하며 적당한 값 찾아간다. 200이면 최대 200단어까지 생성. 
        temperature=1.0, # 창의성 발휘 여부. 0~2 사이. 0에 가까우면 strict하게, 2에 가까우면 자유롭게(창의성 필요)
        stop=None # 특정 문자열이 들어오면 멈춘다든지. None이면 없음. .이면 문장이 끝나면 멈춘다든지
    )
    answer = response.choices[0].message.content