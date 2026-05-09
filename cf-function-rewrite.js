function handler(event) {
    var request = event.request;
    var uri = request.uri;

    // Trailing slash → append index.html
    if (uri.endsWith('/')) {
        request.uri = uri + 'index.html';
    }
    // No extension and no trailing slash → treat as directory, append /index.html
    else if (!uri.includes('.')) {
        request.uri = uri + '/index.html';
    }

    return request;
}
