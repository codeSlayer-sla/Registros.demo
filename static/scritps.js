import React from 'react';
import Home from './Home';

const App = () => {
    const user = { name: 'Megan Bowen' };
    const config = { ENDPOINT: true, B2C_PROFILE_AUTHORITY: 'https://example.com', CLIENT_ID: '12345' };
    const version = '1.0.0';

    return <Home user={user} config={config} version={version} />;
};

export default App;
