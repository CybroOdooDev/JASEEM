/** @odoo-module **/

function navigateToProductList() {
    // Click the Order Products link first
    const orderProductsLink = document.querySelector('a[name="customer_products"]');
    if (orderProductsLink) {
        orderProductsLink.click();

        // Multiple attempts to scroll
        setTimeout(scrollToNotebookStart);
    }
}

function scrollToNotebookStart() {
    // Target the notebook specifically
    const notebook = document.querySelector('.o_notebook');
    if (notebook) {
        // Scroll to the top of the notebook
        notebook.scrollTop = 0;

        // Target the first page/tab in the notebook
        const firstNotebookPage = notebook.querySelector('.tab-pane:first-child');
        if (firstNotebookPage) {
            firstNotebookPage.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }

        // Additional fallback methods
        window.scrollTo({
            top: notebook.offsetTop,
            behavior: 'smooth'
        });
    } else {
        console.log('Notebook not found');
    }
}

// Attach the function to the global window object
window.navigateToProductList = navigateToProductList;