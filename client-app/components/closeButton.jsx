import React        from 'react';


class CloseButton extends React.Component {
    render() {
        return (
            <img className="close-button" onClick={this.props.onClick} src="/img/close.png" />
        )
    }
}

export default CloseButton;