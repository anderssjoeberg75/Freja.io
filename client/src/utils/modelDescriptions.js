export const getModelDescription = (modelId) => {
    if (!modelId) return '';
    const m = modelId.toLowerCase();

    // OpenAI Models
    if (m.startsWith('o1')) return 'Advanced reasoning (OpenAI)';
    if (m.startsWith('o3-mini')) return 'Fast reasoning (OpenAI)';
    if (m.startsWith('gpt-4o-mini')) return 'Fast and affordable (OpenAI)';
    if (m.startsWith('gpt-4o')) return 'All-around & capable (OpenAI)';
    if (m.startsWith('gpt-4-turbo')) return 'Powerful legacy model (OpenAI)';

    // Google Models
    if (m.startsWith('gemini-2.5-pro') || m.startsWith('gemini-2.0-pro')) return 'Advanced logic & analysis (Google)';
    if (m.startsWith('gemini-2.5-flash') || m.startsWith('gemini-2.0-flash')) return 'Fast & multimodal (Google)';
    if (m.startsWith('gemini-1.5')) return 'Legacy multimodal (Google)';

    // Anthropic Models
    if (m.startsWith('claude-3-5-sonnet')) return 'Strong coding & logic (Anthropic)';
    if (m.startsWith('claude-3-opus')) return 'Advanced reasoning (Anthropic)';
    if (m.startsWith('claude-3-haiku')) return 'Fast & lightweight (Anthropic)';

    // DeepSeek Models
    if (m.includes('deepseek-coder')) return 'Specialized for coding';
    if (m.includes('deepseek-r1:1.5b')) return 'Mini-reasoning';
    if (m.includes('deepseek-r1:8b')) return 'Fast reasoning';
    if (m.includes('deepseek-r1:14b')) return 'Heavy reasoning (Qwen based)';
    if (m.includes('deepseek-r1:32b')) return 'Heavyweight reasoning';
    if (m.includes('deepseek-r1:70b')) return 'Gigantic reasoning';
    if (m.includes('deepseek-r1')) return 'Advanced reasoning & logic';

    // Ollama / Open Source
    if (m.includes('qwen2.5-coder')) return 'Excellent coding model';
    if (m.includes('qwen2.5:0.5b')) return 'Tiny but capable';
    if (m.includes('qwen2.5:32b')) return 'Heavyweight model';
    if (m.includes('qwen2.5')) return 'Strong all-around AI';
    if (m.includes('codellama')) return "Meta's coding AI";
    if (m.includes('llama3.3')) return 'Huge & powerful standard';
    if (m.includes('llama3.2:1b')) return 'Ultrafast, mobile-friendly';
    if (m.includes('llama3.2')) return 'Fast standard model';
    if (m.includes('llama3.1:8b')) return 'Great standard model';
    if (m.includes('llama3.1')) return 'Previous classic';
    if (m.includes('mistral')) return 'Classic & reliable';
    if (m.includes('mixtral')) return 'Powerful MoE from Mistral';
    if (m.includes('gemma2:2b') || m.includes('gemma-2:2b')) return 'Small from Google';
    if (m.includes('gemma2') || m.includes('gemma-2')) return "Google's open-weights";
    if (m.includes('phi4') || m.includes('phi-4')) return 'Maxed logic & math (Microsoft)';
    if (m.includes('phi3') || m.includes('phi-3')) return 'Small & capable (Microsoft)';

    return 'Generative AI Model';
};

export const formatModelOption = (modelId) => {
    const desc = getModelDescription(modelId);
    return desc ? `${modelId} - ${desc}` : modelId;
};
