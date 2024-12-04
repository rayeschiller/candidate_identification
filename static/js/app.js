document.addEventListener('DOMContentLoaded', async () => {
    const stateSelect = document.getElementById('state-select');
    const countySelect = document.getElementById('county-select');
    const voterList = document.getElementById('voter-list');

    const getColorClass = (score) => {
        if (score > 80) return 'score-green';
        if (score >= 60) return 'score-yellow';
        return 'score-red';
    };

    async function loadRegions() {
        try {
            const response = await fetch('/api/regions');
            if (!response.ok) throw new Error('Failed to load regions');
            const data = await response.json();

            data.states.forEach(state => {
                const option = document.createElement('option');
                option.value = state;
                option.textContent = state;
                stateSelect.appendChild(option);
            });

            stateSelect.addEventListener('change', () => {
                const selectedState = stateSelect.value;
                countySelect.innerHTML = '';

                data.counties[selectedState]?.forEach(county => {
                    const option = document.createElement('option');
                    option.value = county;
                    option.textContent = county;
                    countySelect.appendChild(option);
                });

                if (countySelect.options.length > 0) {
                    countySelect.value = countySelect.options[0].value;
                }
            });

            if (stateSelect.options.length > 0) {
                stateSelect.value = stateSelect.options[0].value;
                stateSelect.dispatchEvent(new Event('change'));
            }
        } catch (error) {
            console.error(error.message);
        }
    }

    async function fetchSocialProfiles(name, container) {
        console.log('Fetching social profiles for:', name);
        container.innerHTML = '<img src="/static/spinner.gif" alt="Loading..." style="width: 24px; height: 24px;">';
        try {
            const response = await fetch(`/api/social_profiles?name=${encodeURIComponent(name)}`);
            const profiles = await response.json();
            console.log('Profiles received:', profiles);

            if (profiles.error) {
                container.innerHTML = `<p class="text-danger">${profiles.error}</p>`;
            } else if (Object.keys(profiles).length === 0) {
                container.innerHTML = `<p class="text-warning">No profiles found.</p>`;
            } else {
                // Render platform as a label and hyperlink the full name
                container.innerHTML = Object.entries(profiles)
                    .map(([platform, url]) => `<strong>${platform}:</strong> <a href="${url}" target="_blank">${name}</a>`)
                    .join('<br>'); // Join links with line breaks
            }
        } catch (error) {
            container.innerHTML = `<p class="text-danger">Error loading profiles: ${error.message}</p>`;
        }
    }


    async function loadCandidates() {
        voterList.innerHTML = '<p>Loading...</p>';

        const state = stateSelect.value;
        const county = countySelect.value;

        try {
            const response = await fetch(`/api/candidates?state=${state}&county=${county}`);
            const data = await response.json();

            voterList.innerHTML = '';

            if (data.length === 0) {
                voterList.innerHTML = '<p>No candidates found for the selected region.</p>';
                return;
            }

            data.forEach(voter => {
                const voterDiv = document.createElement('div');
                voterDiv.className = 'score-card';

                voterDiv.innerHTML = `
            <div class="d-flex align-items-center mb-3">
    <!-- Picture and Name in One Section -->
    <div class="d-flex align-items-center me-3">
        <img src="${voter.photo}" alt="${voter.name}" class="rounded-circle" width="50" height="50">
        <h5 class="ms-3 mb-0">${voter.name}</h5>
    </div>
    <!-- Overall Score in Another Section -->
    <div>
        <span class="fs-4 fw-bold p-1 custom-rounded ${getColorClass(voter.score)}">Overall Score: ${voter.score}</span>
    </div>
</div>

            <div class="row">
                <div class="col-md-4"><div class="p-2 ${getColorClass(voter.activist_score)}">Activist Score: ${voter.activist_score}</div></div>
                <div class="col-md-4"><div class="p-2 ${getColorClass(voter.partisan_score)}">Partisan Score: ${voter.partisan_score}</div></div>
                <div class="col-md-4"><div class="p-2 ${getColorClass(voter.local_voter_score)}">Local Voter Score: ${voter.local_voter_score}</div></div>
            </div>
            <div class="mt-3">Age: ${voter.age} | Years in Residence: ${voter.years_in_residence}</div>
            <button class="btn btn-secondary mt-3" id="fetch-profile-${voter.name.replace(/\s+/g, '-')}">Load Social Profiles</button>
            <div id="profiles-${voter.name.replace(/\s+/g, '-')}" class="mt-3"></div>
            `;

                voterList.appendChild(voterDiv);

                // Add click listener to the "Load Social Profiles" button
                const profileButton = document.getElementById(`fetch-profile-${voter.name.replace(/\s+/g, '-')}`);
                const profileContainer = document.getElementById(`profiles-${voter.name.replace(/\s+/g, '-')}`);

                profileButton.addEventListener('click', () => {
                    const name = voter.name.replace(/\s+/g, ''); // Join first and last names
                    fetchSocialProfiles(name, profileContainer);
                });
            });
        } catch (error) {
            voterList.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
        }
    }


    await loadRegions();
    document.getElementById('load-button').addEventListener('click', loadCandidates);
});
