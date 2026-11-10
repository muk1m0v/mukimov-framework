const nameField = document.querySelector("#name");
const count = document.querySelector("#name-count");

if (nameField && count) {
    const update = () => {
        count.textContent = `Символов: ${nameField.value.length} из ${nameField.maxLength}`;
    };
    count.hidden = false;
    update();
    nameField.addEventListener("input", update);
}
