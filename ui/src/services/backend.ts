// apiService.ts
export const getPathFromBackend = async (start: [number, number], end: [number, number]) => {
    try {
      const response = await fetch('http://127.0.0.1:3000/get-path', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start: {lat: start[1], lon: start[0]},
          end: {lat: end[1], lon: end[0]},
        }),
      });
  
      if (!response.ok) {
        throw new Error('Failed to fetch path');
      }
  
      return await response.json(); // This should be your path data
    } catch (error) {
      console.error('Error fetching path:', error);
      throw error; // Re-throw error to handle it in the component
    }
  };
  