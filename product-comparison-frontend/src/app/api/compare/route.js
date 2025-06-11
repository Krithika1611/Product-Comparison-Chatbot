import { PythonShell } from 'python-shell';

export async function POST(request) {
  try {
    const { product, chat_history } = await request.json();

    console.log("Received product from frontend:", product);

    const result = await new Promise((resolve, reject) => {
      let pyshell = new PythonShell('app.py', {
        mode: 'text',
        pythonOptions: ['-u'], // unbuffered output
      });

      let responseData = '';

      // Send data as JSON
      const dataToSend = JSON.stringify({ 
        product: product,
        chat_history: chat_history || []
      });
      
      pyshell.send(dataToSend);

      pyshell.on('message', function (message) {
        console.log("Python Message:", message);
        responseData += message + '\n'; // Add newline to separate messages
      });

      pyshell.on('error', function (err) {
        console.error("Python Shell Error:", err);
        reject(err);
      });

      pyshell.end(function (err) {
        if (err) {
          console.error("Python Shell End Error:", err);
          return reject(err);
        }
        console.log("Python response captured:", responseData);
        resolve(responseData.trim()); // Remove any trailing newline
      });
    });

    return new Response(JSON.stringify({
      analysis: result || "No data generated",
      product: product,
      timestamp: new Date().toISOString()
    }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200
    });

  } catch (error) {
    console.error("API Error:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { 'Content-Type': 'application/json' },
      status: 500
    });
  }
}