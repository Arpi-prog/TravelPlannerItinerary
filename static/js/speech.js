var speechSynthesisActive = false;
var textToRead = "";  // Placeholder for the itinerary text

function startReadingItinerary() {
    if (speechSynthesisActive) return;  // Prevent starting another reading

    speechSynthesisActive = true;
    var utterance = new SpeechSynthesisUtterance(textToRead);

    utterance.onend = function () {
        speechSynthesisActive = false;  // Reset after reading
    };

    window.speechSynthesis.speak(utterance);
}

function setItineraryText(itineraryText) {
    textToRead = itineraryText;  // Set the itinerary text to read
}

{% if itinerary %}
    setItineraryText("{{ itinerary }}");
{% endif %}
