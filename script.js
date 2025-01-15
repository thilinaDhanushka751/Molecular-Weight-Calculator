let history = [];

// Function to submit the formula for calculation
async function submitFormula() {
    const formula = document.getElementById('chemicalFormula').value.trim();
    const resultDiv = document.getElementById('result');

    // Check for empty input
    if (!formula) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'alert alert-danger';
        resultDiv.innerText = 'Please enter a chemical formula.';
        return;
    }

    try {
        const response = await fetch('/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ formula })
        });

        if (response.ok) {
            const data = await response.json();
            resultDiv.style.display = 'block';
            resultDiv.className = 'alert alert-success';
            resultDiv.innerText = `Molecular Weight: ${data.molecular_weight.toFixed(2)} amu`;

            // Add to history
            history.push(`${formula}: ${data.molecular_weight.toFixed(2)} amu`);
            updateHistory();
        } else {
            const errorData = await response.json();
            resultDiv.style.display = 'block';
            resultDiv.className = 'alert alert-danger';
            resultDiv.innerText = errorData.error;
        }
    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.className = 'alert alert-danger';
        resultDiv.innerText = 'An unexpected error occurred.';
    }
}

// Function to update the history section
function updateHistory() {
    const historyList = document.getElementById('historyList');
    historyList.innerHTML = ''; // Clear previous history
    history.forEach((item) => {
        const li = document.createElement('li');
        li.textContent = item;
        li.className = 'list-group-item';
        historyList.appendChild(li);
    });
}

// Function to clear input and result fields
function clearFields() {
    document.getElementById('chemicalFormula').value = '';
    document.getElementById('result').style.display = 'none';
    document.getElementById('result').innerText = '';
}
