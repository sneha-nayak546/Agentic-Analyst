import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=14,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        name='SubtitleStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=14,
        textColor=colors.gray
    )
    
    heading_style = ParagraphStyle(
        name='HeadingStyle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.black
    )
    
    body_style = ParagraphStyle(
        name='BodyStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leading=14
    )
    
    verdict_style = ParagraphStyle(
        name='VerdictStyle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=16,
        spaceAfter=16,
        textColor=colors.red,
        alignment=1 # Center
    )

    story = []

    # Title
    story.append(Paragraph("DAILY REPORT", title_style))
    story.append(Paragraph("Prepared by: SNEHA NAYAK AI DEVELOPER", subtitle_style))
    story.append(Spacer(1, 12))

    # Intro
    story.append(Paragraph("This report contains the final analysis of the local CPU benchmark for the JGH Intelligence Engine running Qwen2.5-Coder 7B via vLLM/Ollama. Conclusions are drawn strictly from the measured benchmark data.", body_style))
    story.append(Spacer(1, 12))

    # 1. Results for all 5 queries
    story.append(Paragraph("1. Results for all 5 queries", heading_style))
    story.append(Paragraph("<b>Query 1:</b> What is the total wallet amount across all users? <font color='red'><b>TIMEOUT</b></font> (Pipeline Time: 140,271.84 ms)", body_style))
    story.append(Paragraph("<b>Query 2:</b> Show me the top 5 retailers by revenue in July 2026. <font color='red'><b>TIMEOUT</b></font> (Pipeline Time: 162,310.83 ms)", body_style))
    story.append(Paragraph("<b>Query 3:</b> Which distributors have inactive linked retailers? <font color='red'><b>TIMEOUT</b></font> (Pipeline Time: 144,133.36 ms)", body_style))
    story.append(Paragraph("<b>Query 4:</b> Count the number of users who have more than 5 wallet transactions. <font color='red'><b>TIMEOUT</b></font> (Pipeline Time: 144,034.33 ms)", body_style))
    story.append(Paragraph("<b>Query 5:</b> Show the distributor ID and total balance for the distributor with the highest balance. <font color='red'><b>TIMEOUT</b></font> (Pipeline Time: 145,326.23 ms)", body_style))
    
    # 2. Latency
    story.append(Paragraph("2. Average, Minimum, and Maximum Latency", heading_style))
    story.append(Paragraph("Since all queries failed due to timeouts, these values represent the time until pipeline failure:", body_style))
    story.append(Paragraph("<b>Minimum Latency:</b> 140,271.84 ms", body_style))
    story.append(Paragraph("<b>Maximum Latency:</b> 162,310.83 ms", body_style))
    story.append(Paragraph("<b>Average Latency:</b> 147,215.32 ms", body_style))

    # 3. SQL generation time vs model loading
    story.append(Paragraph("3. SQL Generation Time vs Prompt Processing", heading_style))
    story.append(Paragraph("The preprocessing steps (NLP Intent and Hybrid RAG/Plan) successfully completed. The system consistently crashed/timed out exclusively during the LLM SQL Generation phase. No successful SQL generation times could be recorded because the connection dropped after waiting over 15 seconds for a single response from the model.", body_style))

    # 4. Tokens/sec
    story.append(Paragraph("4. Tokens / Sec", heading_style))
    story.append(Paragraph("<b>0.00 tokens/sec.</b> The model failed to generate or stream any tokens before timing out.", body_style))

    # 5. CPU and RAM usage
    story.append(Paragraph("5. CPU and RAM Usage", heading_style))
    story.append(Paragraph("Usage metrics could not be logged to the final output file because the Python script's pipeline forcefully crashed/timed out prior to the metric collection stage.", body_style))

    # 6. KV/prefix caching
    story.append(Paragraph("6. KV / Prefix Caching Effectiveness", heading_style))
    story.append(Paragraph("Cannot be measured. KV caching requires at least one successful LLM pass to store context, but the system failed to complete a single prompt.", body_style))

    # 7. OLLAMA_NUM_PARALLEL=4 vs 1
    story.append(Paragraph("7. OLLAMA_NUM_PARALLEL=4 vs NUM_PARALLEL=1", heading_style))
    story.append(Paragraph("<b>NUM_PARALLEL=1:</b> Proceeded through the NLP/RAG steps and reached the LLM request phase before timing out at ~140-160 seconds total execution.", body_style))
    story.append(Paragraph("<b>OLLAMA_NUM_PARALLEL=4:</b> Hung indefinitely immediately upon loading weights. Context switching for 4 parallel instances completely stalled the local CPU, preventing any progress.", body_style))

    # 8. Bottleneck
    story.append(Paragraph("8. Biggest Performance Bottleneck", heading_style))
    story.append(Paragraph("The local CPU. Attempting to run a 7-Billion parameter model (Qwen2.5-Coder) entirely on CPU compute lacks the hardware throughput required to stream LLM tokens within standard network connection limits.", body_style))

    # 9. Incorrect SQL
    story.append(Paragraph("9. Incorrect SQL Analysis", heading_style))
    story.append(Paragraph("No SQL was generated to evaluate. Every single query resulted in a Read Timeout error from the LLM.", body_style))

    # 10. Practicality
    story.append(Paragraph("10. Is Qwen2.5-Coder 7B local CPU practical?", heading_style))
    story.append(Paragraph("<b>Absolutely not.</b> The 100% failure rate and excessive latencies demonstrate that this model size is too heavy for local CPU deployment.", body_style))

    # 11. Next steps
    story.append(Paragraph("11. Exact Changes to Make Next", heading_style))
    story.append(Paragraph("1. Switch your local model to a smaller parameter size that the CPU can handle (e.g., <b>Qwen2.5-Coder 1.5B</b> or <b>0.5B</b>) by updating the <code>QWEN_MODEL</code> environment variable.", body_style))
    story.append(Paragraph("2. Ensure <code>OLLAMA_NUM_PARALLEL</code> remains set to 1 for CPU inference to avoid stalling.", body_style))

    # 12. Recommendations
    story.append(Paragraph("12. Infrastructure Recommendations", heading_style))
    story.append(Paragraph("Because the benchmark results genuinely show that local CPU is mathematically insufficient to run a 7B parameter model (0% success rate), if you absolutely require the 7B model's reasoning capabilities, you <b>must</b> migrate the LLM inference to a dedicated Cloud GPU service.", body_style))

    # 13. Verdict
    story.append(Paragraph("VERDICT: NOT SUITABLE FOR LOCAL CPU", verdict_style))
    
    verdict_text = "The Qwen2.5-Coder 7B model completely overwhelms the local CPU hardware, resulting in severe bottlenecks and a 100% timeout failure rate across all benchmark queries. The system is unable to generate a single token within standard connection limits, and parallelizing requests only stalls the system entirely. Therefore, running this 7B model on a local CPU is mathematically insufficient for a production environment."
    story.append(Paragraph(verdict_text, body_style))

    doc.build(story)

if __name__ == '__main__':
    generate_pdf('DAILY_REPORT.pdf')
