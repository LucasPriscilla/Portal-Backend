import React    from 'react';


class EmptyState extends React.Component {
    render() {
        return (
            <div className="empty-state">
                <strong>{this.props.showError ? "No Route Found" : "Let's go"}</strong>
                1. Enter a starting location.<br/>
                2. Enter a destination.<br/>
                3. Find the perfect commute.
            </div>
        )
    }
}

export default EmptyState;
