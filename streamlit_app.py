import streamlit as st
import time
import random
import numpy as np
import nltk
from nltk.tokenize import word_tokenize
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

# Download necessary NLTK data
nltk.download('punkt', quiet=True)

class SimpleLanguageModel:
    def __init__(self):
        self.model = defaultdict(lambda: defaultdict(int))
        self.vocab = set()

    def train(self, text):
        tokens = word_tokenize(text.lower())
        self.vocab.update(tokens)
        for i in range(len(tokens) - 1):
            self.model[tokens[i]][tokens[i + 1]] += 1
        # Find the token with the most transitions
        max_transitions_token = max(self.model, key=lambda k: len(self.model[k]) if self.model[k] else 0)
        max_transitions = self.model[max_transitions_token]
        return tokens, max_transitions_token, max_transitions

    def generate(self, start_token, length=10, temperature=1.0):
        current_token = start_token
        result = [{"token": current_token, "rationale": f"Starting token: '{current_token}'"}]
        for _ in range(length - 1):
            next_token_probs = self.model[current_token]
            if not next_token_probs:
                break
            # Apply temperature
            adjusted_probs = {k: v ** (1 / temperature) for k, v in next_token_probs.items()}
            total = sum(adjusted_probs.values())
            adjusted_probs = {k: v / total for k, v in adjusted_probs.items()}
            next_token = random.choices(list(adjusted_probs.keys()), 
                                        weights=list(adjusted_probs.values()))[0]
            rationale = (
                f"Token: '{next_token}' selected. "
                f"Original probabilities: {next_token_probs}. "
                f"Adjusted probabilities (temperature={temperature}): {adjusted_probs}. "
                f"Temperature of {temperature} {'flattened' if temperature > 1 else 'sharpened' if temperature < 1 else 'maintained'} the probability distribution."
            )
            result.append({"token": next_token, "rationale": rationale})
            current_token = next_token
        return result

def simulate_attention(tokens, output_tokens):
    attention_matrix = [[random.random() for _ in range(len(tokens))] for _ in range(len(output_tokens))]
    for row in attention_matrix:
        total = sum(row)
        for i in range(len(row)):
            row[i] /= total
    return attention_matrix

def main():
    st.title("💻 LLM Simulator App")

    # Initialize or load the language model
    if 'language_model' not in st.session_state:
        st.session_state.language_model = SimpleLanguageModel()

    # Input text
    input_text = st.text_area("Enter your text here:", height=100)

    # Model parameters
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider("Temperature", 0.1, 2.0, 1.0, 0.1)
    with col2:
        output_length = st.slider("Output Length", 5, 50, 20)

    if st.button("Process"):
        if input_text:
            # Tokenization and training
            tokens, max_transitions_token, max_transitions = st.session_state.language_model.train(input_text)
            
            # Store the tokens and generated data in session state to avoid recomputation
            st.session_state.tokens = tokens
            st.session_state.max_transitions_token = max_transitions_token
            st.session_state.max_transitions = max_transitions
            output_with_rationales = st.session_state.language_model.generate(tokens[0], output_length, temperature)
            st.session_state.output_with_rationales = output_with_rationales
            st.session_state.generated_tokens = [entry["token"] for entry in output_with_rationales]
            st.session_state.generated_sentence = " ".join(st.session_state.generated_tokens)
        
    if 'output_with_rationales' in st.session_state:
        st.subheader("LLM Output")
        st.write("Generated Output Sentence:", st.session_state.generated_sentence)

        with st.expander("Output Tokens with Rationales", expanded=True):
            for i, entry in enumerate(st.session_state.output_with_rationales):
                st.write(f"{i}: {entry['token']} - {entry['rationale']}")

        st.subheader("Attention Visualization")
        st.write("The attention visualization shows how each output token attends to each input token.")
        attention_matrix = simulate_attention(st.session_state.tokens, st.session_state.generated_tokens)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(attention_matrix, xticklabels=st.session_state.tokens, yticklabels=st.session_state.generated_tokens, ax=ax, cmap="YlOrRd")
        plt.xlabel("Input Tokens")
        plt.ylabel("Output Tokens")
        st.pyplot(fig)

        st.subheader("Token Probability Visualization")
        st.write("The token probability visualization shows the likelihood of each possible next token given the current token, based on the training data.")
        
        if 'selected_token' not in st.session_state:
            st.session_state.selected_token = None
        
        st.session_state.selected_token = st.selectbox("Select a token to see next token probabilities:", list(st.session_state.language_model.vocab), index=list(st.session_state.language_model.vocab).index(st.session_state.selected_token) if st.session_state.selected_token else 0)

        if st.session_state.selected_token:
            next_token_probs = st.session_state.language_model.model[st.session_state.selected_token]
            adjusted_probs = {k: v ** (1 / temperature) for k, v in next_token_probs.items()}
            total = sum(adjusted_probs.values())
            adjusted_probs = {k: v / total for k, v in adjusted_probs.items()}

            if next_token_probs:
                fig, ax = plt.subplots()
                tokens, probs = zip(*sorted(next_token_probs.items(), key=lambda x: x[1], reverse=True)[:10])
                adj_tokens, adj_probs = zip(*sorted(adjusted_probs.items(), key=lambda x: x[1], reverse=True)[:10])
                bar_width = 0.35
                index = np.arange(len(tokens))
                
                bar1 = ax.bar(index, probs, bar_width, label='Original Probabilities')
                bar2 = ax.bar(index + bar_width, adj_probs, bar_width, label='Adjusted Probabilities (Temperature)')

                plt.xticks(index + bar_width / 2, tokens, rotation=45, ha='right')
                plt.xlabel("Next Tokens")
                plt.ylabel("Probability")
                plt.legend()
                st.pyplot(fig)
            else:
                st.write("No next token probabilities available for the selected token.")

if __name__ == "__main__":
    main()

# Add footer
footer = st.container()
footer.markdown(
    '''
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: black;
        color: white;
        text-align: center;
        padding: 10px 0;
    }
    </style>
    <div class="footer">
        <p>© 2024 Bloch AI LTD - All Rights Reserved. <a href="https://www.bloch.ai" style="color: white;">www.bloch.ai</a></p>
    </div>
    ''',
    unsafe_allow_html=True
)
