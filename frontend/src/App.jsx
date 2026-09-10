import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

function App() {

  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState("Chennai");
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);

  // Get cities
  useEffect(() => {

    axios
      .get("http://127.0.0.1:8000/api/cities")
      .then((response) => {
        setCities(response.data.cities);
      })
      .catch((error) => {
        console.error("Error fetching cities:", error);
      });

  }, []);


  // Get dashboard data
  useEffect(() => {

    if (!selectedCity) {
      return;
    }

    setLoading(true);

    axios
      .get(
        `http://127.0.0.1:8000/api/dashboard/${selectedCity}`
      )
      .then((response) => {
        setDashboard(response.data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching dashboard:", error);
        setLoading(false);
      });

  }, [selectedCity]);


  return (
    <div className="app">

      <header className="header">
        <div>
          <h1>AQI Health Risk System</h1>
          <p>Air Quality Monitoring & TCN Prediction</p>
        </div>

        <div className="city-selector">
          <label>Select City</label>

          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
          >
            {cities.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
        </div>
      </header>


      {loading && (
        <div className="loading">
          Loading AQI data...
        </div>
      )}


      {dashboard && !loading && (

        <main>

          <section className="cards">

            <div className="card">
              <h3>Current AQI</h3>
              <div className="aqi-value">
                {dashboard.current.aqi}
              </div>
              <p>{dashboard.current.category}</p>
            </div>


            <div className="card">
              <h3>Predicted AQI</h3>
              <div className="aqi-value">
                {dashboard.prediction.predicted_aqi}
              </div>
              <p>{dashboard.prediction.category}</p>
            </div>


            <div className="card">
              <h3>Health Risk</h3>
              <div className="risk">
                {dashboard.current.health_risk}
              </div>
              <p>{dashboard.current.health_concern}</p>
            </div>

          </section>


          <section className="pollutants">

            <h2>Pollutant Levels</h2>

            <div className="pollutant-grid">

              <div className="pollutant">
                <span>PM2.5</span>
                <strong>
                  {dashboard.current.pm25}
                </strong>
              </div>

              <div className="pollutant">
                <span>PM10</span>
                <strong>
                  {dashboard.current.pm10}
                </strong>
              </div>

              <div className="pollutant">
                <span>AQI-IN</span>
                <strong>
                  {dashboard.current["AQI-IN"]}
                </strong>
              </div>

            </div>

          </section>


          <section className="health">

            <h2>Health Advisory</h2>

            <p>
              {dashboard.current.health_concern}
            </p>

          </section>

        </main>

      )}

    </div>
  );
}

export default App;