const myInput = document.getElementById('userInput');
const id = document.getElementById("id");
const pokemonInfoElements = document.getElementsByClassName('pokemonInfo');
const description = document.getElementById("descriptionBox");
const movesetButton = document.getElementById("movesetButton");
const detailButton = document.getElementById("detailButton");
const moveListElements = document.getElementsByClassName('moveListInfo');
const generationSelect = document.getElementById('generationSelect');


let minLevel = 1;
let maxLevel = 100;

let twoTimesWeakness = [];
let fourTimesWeakness = [];
let halfResistance = [];
let quarterResistance = [];

let generation = 9;      // default generation is set to 9
let name_global = '';
let id_global = '';


const genMap = {
                'red-blue': 1, 'yellow': 1,
                'gold-silver': 2, 'crystal': 2,
                'ruby-sapphire': 3, 'emerald': 3, 'firered-leafgreen': 3,
                'diamond-pearl': 4, 'platinum': 4, 'heartgold-soulsilver': 4,
                'black-white': 5, 'black-2-white-2': 5,
                'x-y': 6, 'omega-ruby-alpha-sapphire': 6,
                'sun-moon': 7, 'ultra-sun-ultra-moon': 7,
                'sword-shield': 8, 'brilliant-diamond-shining-pearl': 8, 'legends-arceus': 8,
                'scarlet-violet': 9
            };




let isPokemonShiny = false;
const shinyButton = document.getElementById("shinyButton");

const pokemonCryButton = document.getElementById('pokemonCryButton');

const blueLight = document.getElementById('blueCircle');
const lightUpColors = ['#005956', '#00fcf4'];

let colorIndex = 0;
      // set initial generation value

function changeBlueLightColor() {
    blueLight.style.backgroundColor = lightUpColors[colorIndex];
    colorIndex = (colorIndex + 1) % lightUpColors.length;       // cycle through lightUpColors
}

const intervalId = setInterval(changeBlueLightColor, 1000);

async function getPokemonData() {
    const inputValue = myInput.value.trim();
    
    // if function is called, unhide pokemonInfo
    for (let i = 0; i < pokemonInfoElements.length; i++) {
        pokemonInfoElements[i].style.display = 'block';
    }

    if (!inputValue) {
        console.error("No input value was read");
        return;
    }

    const isValidInput = /^[a-zA-Z0-9-]+$/.test(inputValue);

    if (!isValidInput) {
        console.error("Please enter a valid Pokemon ID (number) or name (letters only)");
        return;
    }

    try {
        
        const response = await fetch(`https://pokeapi.co/api/v2/pokemon/${inputValue}/`);
 
            if (!response.ok) {
                throw new Error("Resource could not be fetched");
            }
            
            const data = await response.json();
            console.log(data);      // data will be shown in console

            // for image
            let pokemonSprite = data.sprites.front_default;
            const imageElement = document.getElementById("pokemonSprite");
            const pokeball = document.getElementById("pokeball");
            
            if (pokemonSprite) {
                // if shiny button is active
                if (isPokemonShiny) {
                    pokemonSprite = data.sprites.front_shiny;
                }
                pokeball.style.display = "none";
                imageElement.src = pokemonSprite;
                imageElement.style.display = "block";
            } 
            else {
                imageElement.style.display = "none";
                pokeball.style.display = "block";
            }

            // for descirption
            let pokemonEntry = await getPokemonDescription(data.name);
            // debug
            if (pokemonEntry) {
                console.log(`description: ${pokemonEntry}`);
            }

            // for name
            const name = document.getElementById("name");
            name.textContent = `Name: ${data.name.charAt(0).toUpperCase() + data.name.slice(1)}`;
            name_global = data.name; // name is now a global variable

            // for pokemon ID
            id.textContent = `ID: ${data.id}`;
            id_global = data.id;     // id is now global variable

            // for weight
            const weight = document.getElementById("weight");
            const newWeight = (data.weight * 100) * 0.0022;
            weight.textContent = `Weight: ${newWeight.toFixed(2)} lbs`;

            // for height
            const height = document.getElementById("height");
            const heightInMeters = data.height / 10;
            const heightInFeet = heightInMeters * 3.28084;      // total feet

            const feet = Math.floor(heightInFeet);
            const inches = Math.round((heightInFeet - feet) * 12);      // feet to inches conversion
            height.textContent = `Height: ${feet}'${inches}''`;

            const type = document.getElementById("type");
            const typeNames = data.types.map(typeInfo => {
                const typeName = typeInfo.type.name;
                return typeName.charAt(0).toUpperCase() + typeName.slice(1);
            });
            type.textContent = `Type: ${typeNames.join(', ')}`;

            // for weaknesses, resistances, and immunities

            await getTypeEffectiveness(data.types);

            await getStats(data.stats);

    }
    catch(error) {
        console.error(error);
    }
}

async function getTypeEffectiveness(pokemonTypes) {

    const weaknessesElement = document.getElementById("weaknesses");
    const resistanceElement = document.getElementById("resistances");
    const immunitiesElement = document.getElementById("immunities");

    try {
        // all weaknesses, resistances, immunities
        let allWeaknesses = new Set();
        let allResistances = new Set();
        let allImmunities = new Set();

        // for specific type effectiveness
        let typeEffectiveness = {};

        const allTypes = ["normal", "fire", "water", "electric", "grass", "ice", "fighting", 
                         "poison", "ground", "flying", "psychic", "bug", "rock", "ghost", 
                         "dragon", "dark", "steel", "fairy"];
        
        // start each type effectiveness at 1
        allTypes.forEach(type => {
            typeEffectiveness[type] = 1;
        });

        for (let i = 0; i < pokemonTypes.length; i++) {
            const typeInfo = pokemonTypes[i];

            // debug purposes
            console.log(`Fetching data type: ${typeInfo.type.name}`);

            // fetch type info
            const typeResponse = await fetch(typeInfo.type.url);
            const typeData = await typeResponse.json();

            const weakTo = typeData.damage_relations.double_damage_from;
            weakTo.forEach(weakness => {
                allWeaknesses.add(weakness.name);
                typeEffectiveness[weakness.name] *= 2;
            });

            const resistantTo = typeData.damage_relations.half_damage_from;
            resistantTo.forEach(resistance => {
                allResistances.add(resistance.name);
                typeEffectiveness[resistance.name] *= 0.5;
            });

            const immuneTo = typeData.damage_relations.no_damage_from;
            immuneTo.forEach(immune => {
                allImmunities.add(immune.name);
            });
        }

        // if (allWeaknesses.size > 0) {
        //     const weaknessArray = Array.from(allWeaknesses).map(weakness =>
        //         weakness.charAt(0).toUpperCase() + weakness.slice(1)
        //     );
        //     weaknessesElement.textContent = `Weaknesses: ${weaknessArray.join(', ')}`;
        // }
        // else {
        //     weaknessesElement.textContent = `Weaknesses: none`;
        // }

        twoTimesWeakness = [];
        fourTimesWeakness = [];
        halfResistance = [];
        quarterResistance = [];

        // Seperate weaknesses with multipliers
        Object.keys(typeEffectiveness).forEach(type => {
            if (typeEffectiveness[type] === 4) {
                fourTimesWeakness.push(type.charAt(0).toUpperCase() + type.slice(1));
            }
            else if (typeEffectiveness[type] === 2) {
                twoTimesWeakness.push(type.charAt(0).toUpperCase() + type.slice(1));
            }
            else if (typeEffectiveness[type] === 0.25) {
                quarterResistance.push(type.charAt(0).toUpperCase() + type.slice(1));
            }
            else if (typeEffectiveness[type] === 0.5) {
                halfResistance.push(type.charAt(0).toUpperCase() + type.slice(1));
            }

        });


        let weaknessText = "Weaknesses: ";
        
        // if fourTimes array is greater than 0, add in to textContent
        // if twoTimes element is detected after fourTimes array, add comma to seperate
        if (fourTimesWeakness.length > 0) {
            weaknessText += fourTimesWeakness.map(type => `${type} (4x)`).join(', ');
            if (twoTimesWeakness.length > 0) {
                weaknessText += ", ";
            }
        }
        
        if (twoTimesWeakness.length > 0) {
            weaknessText += twoTimesWeakness.map(type => `${type} (2x)`).join(', ');
        }
        
        if (fourTimesWeakness.length === 0 && twoTimesWeakness.length === 0) {
            weaknessText += "None";
        }


        weaknessesElement.textContent = weaknessText;


        // For now it will only print out resistances
        // if (allResistances.size > 0) {
        //     const resistanceArray = Array.from(allResistances).map(resistance =>
        //         resistance.charAt(0).toUpperCase() + resistance.slice(1)
        //     );
        //     resistancesElement.textContent = `Resistances: ${resistanceArray.join(', ')}`;
        // }
        // else {
        //     resistancesElement.textContent = `Resistances: none`;
        // }


        let resistanceText = "Resistances: ";

        if (quarterResistance.length > 0) {
            resistanceText += quarterResistance.map(type => `${type} (0.25)`).join(', ');
            if (halfResistance.length > 0) {
                resistanceText += ', ';
            }
        }

        if (halfResistance.length > 0) {
            resistanceText += halfResistance.map(type => `${type} (0.5)`).join(', ');
        }

        if (halfResistance.length === 0 && quarterResistance.length === 0) {
            resistanceText += "None";
        }

        resistanceElement.textContent = resistanceText;



        if (allImmunities.size > 0) {
            const immunityArray = Array.from(allImmunities).map(immunity =>
                immunity.charAt(0).toUpperCase() + immunity.slice(1)
            );
            immunitiesElement.textContent = `Immunities: ${immunityArray.join(', ')}`;
        }
        else {
            immunitiesElement.textContent = `Immunities: None`;
        }

    }
    catch(error) {
        console.error(error);
    }
}


async function getStats(pokemonStats) {
    
    const hpDisplay = document.getElementById('statLabelHP');
    const attackDisplay = document.getElementById('statLabelAttack');
    const defenseDisplay = document.getElementById('statLabelDefense');
    const specialAttackDisplay = document.getElementById('statLabelSpecialAttack');
    const specialDefenseDisplay = document.getElementById('statLabelSpecialDefense');
    const speedDisplay = document.getElementById('statLabelSpeed');

    try {

        // add values to a map; set name and base stat
        const stats = pokemonStats.map(statInfo => ({
            name: statInfo.stat.name,
            base_stat: statInfo.base_stat
        }));

        // for debug
        stats.forEach(stat => {
            console.log(`${stat.name}: ${stat.base_stat}`);
        });

        // find stat name to get data
        const hpStat = stats.find(stat => stat.name === 'hp');
        const attackStat = stats.find(stat => stat.name === 'attack');
        const defenseStat = stats.find(stat => stat.name === 'defense');
        const specialAttackStat = stats.find(stat => stat.name === 'special-attack');
        const specialDefenseStat = stats.find(stat => stat.name === 'special-defense');
        const speedStat = stats.find(stat => stat.name === 'speed');

        hpDisplay.textContent = `HP: ${hpStat.base_stat}`;
        attackDisplay.textContent = `Attack: ${attackStat.base_stat}`;
        defenseDisplay.textContent = `Defense: ${defenseStat.base_stat}`;
        specialAttackDisplay.textContent = `Special Attack: ${specialAttackStat.base_stat}`;
        specialDefenseDisplay.textContent = `Special Defense: ${specialDefenseStat.base_stat}`;
        speedDisplay.textContent = `Speed: ${speedStat.base_stat}`;

        // change box colors accordingly
        lightUpBoxes('hp', hpStat.base_stat);
        lightUpBoxes('attack', attackStat.base_stat);
        lightUpBoxes('defense', defenseStat.base_stat);
        lightUpBoxes('specialAttack', specialAttackStat.base_stat);
        lightUpBoxes('specialDefense', specialDefenseStat.base_stat);
        lightUpBoxes('speed', speedStat.base_stat);


        return stats;
    }
    catch(error) {
        console.error(error);
    }
}

function lightUpBoxes(statName, statValue) {
    const pointsPerBox = 17;        // max number for each box
    const boxesToLight = Math.min(Math.ceil(statValue / pointsPerBox), 15);     // get how many boxes needed to be lit up

    const statBoxes = document.querySelectorAll(`.${statName}Box`);
    // reverse array to display boxes from bottom to top
    const statsArray = Array.from(statBoxes);
    statsArray.reverse();

    // indexes each box from each stat column
    statsArray.forEach((box, index) => {
        if (index < boxesToLight) {
            box.classList.add('lit');
        }
        else {
            box.classList.remove('lit');
        }
    });

}

function playPokemonSound(pokemonId) {
    const pokemonCry = `https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/${pokemonId}.ogg`
    const pokemonAudio = new Audio(pokemonCry);
    pokemonAudio.volume = 0.25;
    pokemonAudio.play();
}

async function getPokemonDescription(pokemonName) {

    try {
        const response = await fetch(`https://pokeapi.co/api/v2/pokemon/${pokemonName}/`);

        if (!response.ok) {
            throw new Error("Resource could not be fetched");
        }

        const data = await response.json();

        const speciesResponse = await fetch(data.species.url);
        if (!speciesResponse.ok) {
            throw new Error("Error occured, as species data could not be fetched");
        }
        const speciesData = await speciesResponse.json();

        const entriesForGeneration = speciesData.flavor_text_entries.filter(entry => {
            if (entry.language.name !== 'en') {
                return false;
            }
            
            // Map version names to generations
            const version = genMap[entry.version.name];
            return version === generation;
        });

        // If no entries found for selected generation, fall back to any English entry
        const englishEntry = entriesForGeneration.length > 0 
            ? entriesForGeneration[0]
            : speciesData.flavor_text_entries.find(entry => entry.language.name === 'en');

        if (!englishEntry) {
            description.textContent = "No description available.";
            return null;
        }

         const cleanDescription = englishEntry.flavor_text
            .replace(/\f/g, ' ')  // Replace form feed characters
            .replace(/\n/g, ' ')  // Replace newlines
            .replace(/\s+/g, ' ') // Replace multiple spaces with single space
            .trim();
        
        description.textContent = cleanDescription;
        return cleanDescription;
    }
    catch(error) {
        console.error(error);
    }
}

async function showMoveList(pokemonName) {

    try {
        const response = await fetch(`https://pokeapi.co/api/v2/pokemon/${pokemonName}/`);

        if (!response.ok) {
            throw new Error("Error occured while fetching data!");
        }
        const data = await response.json();
        console.log(data.moves);


        // hide pokemonInfo to make room for move list
        for (let i = 0; i < pokemonInfoElements.length; i++) {
            pokemonInfoElements[i].style.display = 'none';
        }

        for (let j = 0; j < moveListElements.length; j++) {
            moveListElements[j].style.display = 'block';
        }

        minLevel = await getMinimumLevel(pokemonName);
        console.log(`Minimum Level: ${minLevel}`);

        const movesByMethod = {
            'level-up': [],
            'machine': [],
            'tutor': [],
            'egg': [],
            'other': []
        };

        data.moves.forEach(moveEntry => {
            const moveName = moveEntry.move.name;
            const formatMoveName = moveName.charAt(0).toUpperCase() + moveName.slice(1).replace(/-/g, ' ');

            const version = moveEntry.version_group_details.find(version => {
                return genMap[version.version_group.name] === generation;
            });

            if (!version) {
                return;
            }

            const learnMethod = version.move_learn_method.name;
            let levelLearned = version.level_learned_at;
            

            const moveInfo = {
                name: formatMoveName,
                level: levelLearned,
                method: learnMethod
            };


            if (learnMethod === 'level-up') {
                movesByMethod['level-up'].push(moveInfo);
            }
            else if (learnMethod === 'machine') {
                movesByMethod['machine'].push(moveInfo);
            }
            else if (learnMethod === 'tutor') {
                movesByMethod['tutor'].push(moveInfo);
            }
            else if (learnMethod === 'egg') {
                movesByMethod['egg'].push(moveInfo);
            }
            else {
                movesByMethod['other'].push(moveInfo);
            }
        });


        // fallback for when no moves are found in selected generation
        // const totalMoves = Object.values(movesByMethod).reduce((sum, arr) => sum + arr.length, 0);
        
        // if (totalMoves === 0) {
        //     console.log(`No moves found for generation ${generation}, using latest available generation`);
            
        //     data.moves.forEach(moveEntry => {
        //         const moveName = moveEntry.move.name;
        //         const formatMoveName = moveName.charAt(0).toUpperCase() + moveName.slice(1).replace(/-/g, ' ');

        //         // Get the latest version (last in array)
        //         const version = moveEntry.version_group_details[moveEntry.version_group_details.length - 1];

        //         const learnMethod = version.move_learn_method.name;
        //         let levelLearned = version.level_learned_at;
                

        //         const moveInfo = {
        //             name: formatMoveName,
        //             level: levelLearned,
        //             method: learnMethod
        //         };


        //         if (learnMethod === 'level-up') {
        //             movesByMethod['level-up'].push(moveInfo);
        //         }
        //         else if (learnMethod === 'machine') {
        //             movesByMethod['machine'].push(moveInfo);
        //         }
        //         else if (learnMethod === 'tutor') {
        //             movesByMethod['tutor'].push(moveInfo);
        //         }
        //         else if (learnMethod === 'egg') {
        //             movesByMethod['egg'].push(moveInfo);
        //         }
        //         else {
        //             movesByMethod['other'].push(moveInfo);
        //         }
        //     });
        // }



        movesByMethod['level-up'].sort((a, b) => a.level - b.level);

        movesByMethod['machine'].sort((a, b) => a.name.localeCompare(b.name));
        movesByMethod['tutor'].sort((a, b) => a.name.localeCompare(b.name));
        movesByMethod['egg'].sort((a, b) => a.name.localeCompare(b.name));
        movesByMethod['other'].sort((a, b) => a.name.localeCompare(b.name));


        let moveListText = ' ';

        if (movesByMethod['level-up'].length > 0) {
            moveListText += 'Level-Up Moves: ';
            moveListText += movesByMethod['level-up'].map(move =>
                move.level > 0 ? `${move.name} (Lv.${move.level})` : `${move.name}`
            ).join(', ');
            moveListText += '\n\n';
        }   
        if (movesByMethod['machine'].length > 0) {
            moveListText += 'TM/HM Moves: ';
            moveListText += movesByMethod['machine'].map(move => move.name).join(', ');
            moveListText += '\n\n';
        }
        if (movesByMethod['tutor'].length > 0) {    
            moveListText += 'Tutor Moves: ';
            moveListText += movesByMethod['tutor'].map(move => move.name).join(', ');
            moveListText += '\n\n';
        }
        if (movesByMethod['egg'].length > 0) {
            moveListText += 'Egg Moves: ';
            moveListText += movesByMethod['egg'].map(move => move.name).join(', ');
            moveListText += '\n\n';
        }
        if (movesByMethod['other'].length > 0) {
            moveListText += 'Other Moves: ';
            moveListText += movesByMethod['other'].map(move => move.name).join(', ');
        }

        moveListText = moveListText.trim();

        console.log('organized Moves: ', movesByMethod);
        
        if (moveListText) {
            for (let i = 0; i < moveListText.length; i++) {
                moveListElements[i].innerHTML = moveListText.replace(/\n/g, '<br>');
            }
        }
        else {
            for (let i = 0; i < moveListElements.length; i++) {
                moveListElements[i].textContent = 'Move List: Pokemon not found in this generation';
            }
        }


        
        // let allMoves = [];

        // data.moves.forEach(moveEntry => {
        //     const moveName = moveEntry.move.name;
        //     allMoves.push(moveName.charAt(0).toUpperCase() + moveName.slice(1).replace(/-/g, ' '));
        // });

        // // debug purposes
        // console.log(allMoves);

        // if (allMoves.length > 0) {
        //     const moveListText = `Move List: ${allMoves.join(', ')}`;
        //     for (let i = 0; i < moveListElements.length; i++) {
        //         moveListElements[i].textContent = moveListText;
        //     }
        // }
        // else {
        //     for (let i = 0; i < moveListElements.length; i++) {
        //         moveListElements[i].textContent = 'Move List: none';
        //     }
        // }

    }
    catch(error) {
        console.log(error);
    }
    
}

function getGeneration() {

    const selectedGeneration = Number(generationSelect.value);

    switch (selectedGeneration) {
        case 1:
            generation = 1;
            break;
        case 2:
            generation = 2;
            break;
        case 3:
            generation = 3;
            break;
        case 4:
            generation = 4;
            break;
        case 5:
            generation = 5;
            break;
        case 6:
            generation = 6;
            break;
        case 7:
            generation = 7;
            break;
        case 8:
            generation = 8;
            break;
        case 9:
            generation = 9;
            break;
        default:
            generation = 9;
    }
    console.log(`Generation set to: ${generation}`);
    
}





async function getMinimumLevel(pokemonName) {
    try {
        // Fetch species data

        const response = await fetch(`https://pokeapi.co/api/v2/pokemon/${pokemonName}/`);
        if (!response.ok) {
            throw new Error("Resource could not be fetched");
        }
        const data = await response.json();

        const speciesResponse = await fetch(data.species.url);
        const speciesData = await speciesResponse.json();
        
        // Fetch evolution chain
        const evolutionResponse = await fetch(speciesData.evolution_chain.url);
        const evolutionData = await evolutionResponse.json();
        
        // Function to traverse the evolution chain
        function findMinLevel(chain, targetName, currentMinLevel = 1) {
            // Check if this is the Pokemon we're looking for
            if (chain.species.name === targetName) {
                return currentMinLevel;
            }
            
            // Check all evolution paths
            for (const evolution of chain.evolves_to) {
                // Get the evolution trigger details
                let evolutionLevel = currentMinLevel;
                
                if (evolution.evolution_details.length > 0) {
                    const details = evolution.evolution_details[0];
                    
                    // If it evolves by level, get that level
                    if (details.min_level) {
                        evolutionLevel = details.min_level;
                    }
                }
                
                // Recursively check this evolution path
                const result = findMinLevel(evolution, targetName, evolutionLevel);
                if (result !== null) {
                    return result;
                }
            }
            
            return null;
        }
        
        const minLevel = findMinLevel(evolutionData.chain, data.name);
        return minLevel || 1; // Default to 1 if not found
        
    } catch (error) {
        console.error('Error fetching evolution data:', error);
        return 1; // Default to level 1 on error
    }
}




function shinySprite() {
    shinyButton.classList.toggle('active');
    isPokemonShiny = shinyButton.classList.contains('active');
}

function showPokemonInfo() {
    for (let j = 0; j < moveListElements.length; j++) {
        moveListElements[j].style.display = 'none';
    }

    for (let i = 0; i < pokemonInfoElements.length; i++) {
        pokemonInfoElements[i].style.display = 'block';
    }
}




generationSelect.addEventListener('change', () => {
    getGeneration();

    if (name_global) {
        getPokemonData();
        getPokemonDescription(name_global)
        for (let j = 0; j < moveListElements.length; j++) {
            moveListElements[j].style.display = 'none';
        }
    }
});


myInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        getPokemonData();
        for (let j = 0; j < moveListElements.length; j++) {
            moveListElements[j].style.display = 'none';
        }
    }
});

shinyButton.addEventListener('click', () => {
    shinySprite();
    getPokemonData();
});

pokemonCryButton.addEventListener('click', () => {
    playPokemonSound(id_global);
});

movesetButton.addEventListener('click', () => {
    showMoveList(name_global);
});

detailButton.addEventListener('click', () => {
    showPokemonInfo();
});