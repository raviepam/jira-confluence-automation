const form = document.getElementById('chat-form');
const promptInput = document.getElementById('prompt');
const responseBox = document.getElementById('response');

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const prompt = promptInput.value.trim();
  if (!prompt) {
    responseBox.textContent = 'Please enter a prompt before sending.';
    return;
  }

  responseBox.textContent = 'Thinking...';

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });

    if (!response.ok) {
      throw new Error('Something went wrong.');
    }

    const data = await response.json();
    responseBox.textContent = data.message;
  } catch (error) {
    responseBox.textContent = 'Unable to reach the local GenAI server.';
    console.error(error);
  }
});
