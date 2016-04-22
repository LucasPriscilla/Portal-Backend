import React            from 'react';
import ReactDOM         from 'react-dom';
import MainView         from '../components/mainView';


window.jQuery = require('jquery');
ReactDOM.render(
    <MainView />,
    document.getElementById('view')
);
